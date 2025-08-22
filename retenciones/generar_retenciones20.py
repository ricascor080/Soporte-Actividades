# -*- coding: utf-8 -*-
import base64, os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from lxml import etree

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import (
    load_der_private_key, load_pem_private_key
)

# ========= RUTAS (ajusta a tu entorno) =========
CER_PATH = r"CSD_Sucursal_1_EKU9003173C9_20230517_223850.cer"
KEY_PATH = r"CSD_Sucursal_1_EKU9003173C9_20230517_223850.key"
KEY_PASS = "12345678a"

XSLT_LOCAL = r"C:\Users\ricas\Downloads\CFDI\retenciones\retencionpago20.xslt"
XSD_PATH   = r"C:\Users\ricas\Downloads\CFDI\retenciones\retencionpagov2.xsd"
OUT_XML    = "retenciones20_sin_timbrar.xml"

# ========= Namespaces / schemaLocation =========
NS = {
    "retenciones": "http://www.sat.gob.mx/esquemas/retencionpago/2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
SCHEMA_LOCATION = (
    "http://www.sat.gob.mx/esquemas/retencionpago/2 "
    "http://www.sat.gob.mx/esquemas/retencionpago/2/retencionpagov2.xsd"
)

# ========= Utilidades =========
def _fmt2(v):
    q = Decimal(str(v))
    return format(q.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")

def load_cert_info(cer_path):
    """Regresa (no_certificado_20_digitos, certificado_base64)."""
    with open(cer_path, "rb") as f:
        der = f.read()
    cert = x509.load_der_x509_certificate(der)

    # Heurística para obtener los 20 dígitos como los espera el SAT:
    hex_serial = format(cert.serial_number, "x")
    if len(hex_serial) % 2:
        hex_serial = "0" + hex_serial
    try:
        ascii_text = bytes.fromhex(hex_serial).decode("ascii", errors="ignore")
        digits = "".join(ch for ch in ascii_text if ch.isdigit())
        no_cert = digits[-20:] if len(digits) >= 20 else digits.zfill(20)
    except Exception:
        no_cert = str(cert.serial_number)[-20:].zfill(20)

    cert_b64 = base64.b64encode(der).decode("ascii")
    return no_cert, cert_b64

def load_private_key_any(path, password: str | None):
    with open(path, "rb") as f:
        data = f.read()
    pw = password.encode("utf-8") if password else None
    try:
        return load_der_private_key(data, pw)
    except Exception:
        pass
    try:
        return load_pem_private_key(data, pw)
    except Exception:
        pass
    raise ValueError("No se pudo cargar la llave privada. Verifica formato y contraseña.")

def sign_sha256_rsa_pkcs1v15(key_path, password, cadena):
    private_key = load_private_key_any(key_path, password)
    firma = private_key.sign(cadena.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    return base64.b64encode(firma).decode("ascii")

def cadena_original_from_xml(xml_tree, xslt_path):
    if not os.path.exists(xslt_path):
        raise FileNotFoundError(f"No se encontró el XSLT: {xslt_path}")
    xslt = etree.parse(xslt_path)
    transform = etree.XSLT(xslt)
    return str(transform(xml_tree))

def save_xml(root, out_path):
    etree.ElementTree(root).write(out_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)

def validar_xsd_verbose(xml_path, xsd_path):
    try:
        schema = etree.XMLSchema(etree.parse(xsd_path))
        doc = etree.parse(xml_path)
        ok = schema.validate(doc)
        if not ok:
            print("❌ Errores XSD:")
            for e in schema.error_log:
                print(f"L{e.line}: {e.message}")
        else:
            print("✔ XML válido contra XSD")
        return ok
    except Exception as ex:
        print("No se pudo validar contra XSD:", ex)
        return False

# ========= Constructor Retenciones 2.0 =========
def build_retenciones_xml(data, no_cert, cert_b64):
    E = etree.Element
    RNS = NS["retenciones"]

    ret = E(f"{{{RNS}}}Retenciones", nsmap=NS)
    ret.set("Version", "2.0")
    ret.set("FechaExp", data.get("FechaExp") or datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    ret.set("CveRetenc", data["CveRetenc"])
    ret.set("LugarExpRetenc", data["LugarExpRetenc"])

    if data.get("FolioInt"):
        # SIN guiones: patrón [0-9a-zA-Z]{1,20}
        ret.set("FolioInt", data["FolioInt"])

    if data.get("DescRetenc"):
        ret.set("DescRetenc", data["DescRetenc"])

    # Atributos exigidos por el XSD Retenciones 2.0
    ret.set("Sello", "")
    ret.set("NoCertificado", no_cert)   # nombre correcto
    ret.set("Certificado", cert_b64)    # nombre correcto

    ret.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", SCHEMA_LOCATION)

    # Emisor
    em = E(f"{{{RNS}}}Emisor")
    em.set("RfcE", data["Emisor"]["RfcE"])
    em.set("NomDenRazSocE", data["Emisor"]["NomDenRazSocE"])
    em.set("RegimenFiscalE", data["Emisor"]["RegimenFiscalE"])
    ret.append(em)

    # Receptor
    rc = E(f"{{{RNS}}}Receptor")
    rc.set("NacionalidadR", data["Receptor"]["NacionalidadR"])
    if data["Receptor"]["NacionalidadR"] == "Nacional":
        na = E(f"{{{RNS}}}Nacional")
        na.set("RfcR", data["Receptor"]["RfcR"])
        na.set("NomDenRazSocR", data["Receptor"]["NomDenRazSocR"])
        na.set("DomicilioFiscalR", data["Receptor"]["DomicilioFiscalR"])
        if data["Receptor"].get("CurpR"):
            na.set("CurpR", data["Receptor"]["CurpR"])
        rc.append(na)
    else:
        ex = E(f"{{{RNS}}}Extranjero")
        ex.set("NomDenRazSocR", data["Receptor"]["NomDenRazSocR"])
        if data["Receptor"].get("NumRegIdTribR"):
            ex.set("NumRegIdTribR", data["Receptor"]["NumRegIdTribR"])
        rc.append(ex)
    ret.append(rc)

    # Periodo
    per = E(f"{{{RNS}}}Periodo")
    per.set("MesIni", data["Periodo"]["MesIni"])
    per.set("MesFin", data["Periodo"]["MesFin"])
    per.set("Ejercicio", data["Periodo"]["Ejercicio"])
    ret.append(per)

    # Totales
    tot = E(f"{{{RNS}}}Totales")
    tot.set("MontoTotOperacion", _fmt2(data["Totales"]["MontoTotOperacion"]))
    tot.set("MontoTotGrav",      _fmt2(data["Totales"]["MontoTotGrav"]))
    tot.set("MontoTotExent",     _fmt2(data["Totales"]["MontoTotExent"]))
    tot.set("MontoTotRet",       _fmt2(data["Totales"]["MontoTotRet"]))
    if data["Totales"].get("UtilidadBimestral"):
        tot.set("UtilidadBimestral", _fmt2(data["Totales"]["UtilidadBimestral"]))
    if data["Totales"].get("ISRCorrespondiente"):
        tot.set("ISRCorrespondiente", _fmt2(data["Totales"]["ISRCorrespondiente"]))

    for it in data["Totales"].get("ImpRetenidos", []):
        ir = E(f"{{{RNS}}}ImpRetenidos")
        if it.get("BaseRet"):     ir.set("BaseRet", _fmt2(it["BaseRet"]))
        if it.get("ImpuestoRet"): ir.set("ImpuestoRet", it["ImpuestoRet"])
        ir.set("MontoRet", _fmt2(it["MontoRet"]))
        ir.set("TipoPagoRet", it["TipoPagoRet"])
        tot.append(ir)
    ret.append(tot)

    return ret

# ========= MAIN =========
if __name__ == "__main__":
    datos = {
        "FechaExp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "CveRetenc": "01",           # Servicios profesionales (válido)
        "LugarExpRetenc": "01000",
        "FolioInt": "R0001",         # SIN guión para pasar el XSD
        "Emisor": {
            "RfcE": "EKU9003173C9",
            "NomDenRazSocE": "ESCUELA KEMPER URGATE",
            "RegimenFiscalE": "601",
        },
        "Receptor": {
            "NacionalidadR": "Nacional",
            "RfcR": "XAXX010101000",
            "NomDenRazSocR": "PÚBLICO EN GENERAL",  # forzado abajo también
            "DomicilioFiscalR": "01000",
        },
        "Periodo": {"MesIni": "01", "MesFin": "01", "Ejercicio": "2025"},
        "Totales": {
            "MontoTotOperacion": "1000.00",
            "MontoTotGrav": "1000.00",
            "MontoTotExent": "0.00",
            "MontoTotRet": "100.00",
            "ImpRetenidos": [
                {"BaseRet": "1000.00", "ImpuestoRet": "001", "MontoRet": "100.00", "TipoPagoRet": "01"}
            ],
        },
    }

    # Normaliza el nombre cuando es RFC genérico nacional (evita Reten20116)
    if datos["Receptor"]["RfcR"].upper() == "XAXX010101000":
        datos["Receptor"]["NomDenRazSocR"] = "PUBLICO EN GENERAL"

    # 1) NoCertificado / Certificado
    no_cert, cert_b64 = load_cert_info(CER_PATH)

    # 2) Construir sin sello (pero con NoCertificado/Certificado)
    root = build_retenciones_xml(datos, no_cert, cert_b64)

    # 3) Cadena original (XSLT local oficial)
    cadena = cadena_original_from_xml(root, XSLT_LOCAL)

    # 4) Firmar (Sello)
    sello_b64 = sign_sha256_rsa_pkcs1v15(KEY_PATH, KEY_PASS, cadena)
    root.set("Sello", sello_b64)

    # 5) Guardar
    save_xml(root, OUT_XML)
    print(f"✅ XML generado: {OUT_XML}")

    # 6) Validación local (opcional pero recomendado)
    if os.path.exists(XSD_PATH):
        validar_xsd_verbose(OUT_XML, XSD_PATH)
    else:
        print("⚠ No se validó contra XSD (no se encontró el archivo).")
