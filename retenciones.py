# -*- coding: utf-8 -*-
import base64
import os
import urllib.request
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from lxml import etree

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_der_private_key, load_pem_private_key

# ----------------- NAMESPACES Y CONSTANTES -----------------
NS = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "pago20": "http://www.sat.gob.mx/Pagos20",
}
SCHEMA_LOCATION = (
    "http://www.sat.gob.mx/cfd/4 "
    "http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd "
    "http://www.sat.gob.mx/Pagos20 "
    "http://www.sat.gob.mx/sitio_internet/cfd/Pagos20/Pagos20.xsd"
)

SAT_XSLT_URL = "https://www.sat.gob.mx/sitio_internet/cfd/4/cadenaoriginal_4_0/cadenaoriginal_4_0.xslt"
XSLT_LOCAL   = "cadenaoriginal_4_0.xslt"

# ----------------- UTILIDADES -----------------
def ensure_file(local_path, url):
    if os.path.exists(local_path):
        return local_path
    print(f"Descargando {os.path.basename(local_path)} …")
    urllib.request.urlretrieve(url, local_path)
    return local_path

def _fmt2(v):
    q = Decimal(str(v))
    return format(q.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")

def load_cert_info(cer_path):
    """
    Devuelve (no_certificado_20digs, certificado_base64) correctos para CFDI.
    Extrae los 20 dígitos ASCII embebidos en el serial del CSD (usado por SAT).
    """
    with open(cer_path, "rb") as f:
        der = f.read()
    cert = x509.load_der_x509_certificate(der)

    hex_serial = format(cert.serial_number, "x")
    if len(hex_serial) % 2 == 1:
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
    raise ValueError("No se pudo cargar la llave privada. Verifica formato/contraseña.")

def sign_cadena(key_path, password, cadena):
    private_key = load_private_key_any(key_path, password)
    signature = private_key.sign(
        cadena.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode("ascii")

def cadena_original_from_xml(xml_tree, xslt_path):
    xslt = etree.parse(xslt_path)
    transform = etree.XSLT(xslt)
    result = transform(xml_tree)
    return str(result)

def save_xml(xml_tree, out_path):
    etree.ElementTree(xml_tree).write(out_path, encoding="UTF-8", xml_declaration=True, pretty_print=True)

# ----------------- CONSTRUCCIÓN CFDI PAGO 2.0 -----------------
def build_cfdi_pago20_xml(data, no_certificado, certificado_b64):
    """
    Construye un CFDI 4.0 de Pagos (Complemento Pagos 2.0) SIN sello.
    Llena NoCertificado y Certificado (requeridos para la cadena).
    """
    E = etree.Element
    cfdi = "{%s}" % NS["cfdi"]
    pago = "{%s}" % NS["pago20"]

    # Comprobante tipo "P" (pagos)
    comprobante = E(cfdi + "Comprobante", nsmap=NS)
    comprobante.set("Version", "4.0")
    if data.get("Serie"): comprobante.set("Serie", data["Serie"])
    if data.get("Folio"): comprobante.set("Folio", data["Folio"])
    comprobante.set("Fecha", data.get("Fecha") or datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    comprobante.set("SubTotal", "0")
    comprobante.set("Moneda", "XXX")
    comprobante.set("Total", "0")
    comprobante.set("TipoDeComprobante", "P")
    comprobante.set("Exportacion", data.get("Exportacion", "01"))
    comprobante.set("LugarExpedicion", data["LugarExpedicion"])
    comprobante.set("Sello", "")  # se llena después
    comprobante.set("NoCertificado", no_certificado)
    comprobante.set("Certificado", certificado_b64)
    comprobante.set("{%s}schemaLocation" % NS["xsi"], SCHEMA_LOCATION)

    # Emisor
    emisor = E(cfdi + "Emisor")
    emisor.set("Rfc", data["Emisor"]["Rfc"])
    if data["Emisor"].get("Nombre"):
        emisor.set("Nombre", data["Emisor"]["Nombre"])
    emisor.set("RegimenFiscal", data["Emisor"]["RegimenFiscal"])
    comprobante.append(emisor)

    # Receptor (UsoCFDI = CP01)
    receptor = E(cfdi + "Receptor")
    receptor.set("Rfc", data["Receptor"]["Rfc"])
    if data["Receptor"].get("Nombre"):
        receptor.set("Nombre", data["Receptor"]["Nombre"])
    receptor.set("DomicilioFiscalReceptor", data["Receptor"]["DomicilioFiscalReceptor"])
    receptor.set("RegimenFiscalReceptor", data["Receptor"]["RegimenFiscalReceptor"])
    receptor.set("UsoCFDI", "CP01")
    comprobante.append(receptor)

    # Conceptos (único concepto de pago)
    conceptos = E(cfdi + "Conceptos")
    concepto = E(cfdi + "Concepto")
    concepto.set("ClaveProdServ", "84111506")
    concepto.set("Cantidad", "1")
    concepto.set("ClaveUnidad", "ACT")
    concepto.set("Descripcion", "Pago")
    concepto.set("ValorUnitario", "0")
    concepto.set("Importe", "0")
    concepto.set("ObjetoImp", "01")  # No objeto de impuesto
    conceptos.append(concepto)
    comprobante.append(conceptos)

    # Complemento pagos 2.0
    complemento = E(cfdi + "Complemento")
    pagos = E(pago + "Pagos")
    pagos.set("Version", "2.0")

    # (Opcional) pago20:Totales -> sólo si hay impuestos en el pago; en ejemplo simple lo omitimos

    # Cada pago realizado (pueden ser varios)
    for p in data["Pagos"]:
        pnode = E(pago + "Pago")
        pnode.set("FechaPago", p["FechaPago"])                 # ej. "2025-08-11T20:10:00"
        pnode.set("FormaDePagoP", p["FormaDePagoP"])           # ej. "03" Transferencia
        pnode.set("MonedaP", p["MonedaP"])                     # "MXN"
        if p.get("TipoCambioP"):
            pnode.set("TipoCambioP", p["TipoCambioP"])
        pnode.set("Monto", _fmt2(p["Monto"]))

        # Documentos relacionados (al menos uno, con UUID de la factura PPD)
        for d in p["DoctosRelacionados"]:
            dnode = E(pago + "DoctoRelacionado")
            dnode.set("IdDocumento", d["IdDocumento"])                 # UUID de la factura a pagar
            if d.get("Serie"): dnode.set("Serie", d["Serie"])
            if d.get("Folio"): dnode.set("Folio", d["Folio"])
            dnode.set("MonedaDR", d["MonedaDR"])                       # "MXN"
            dnode.set("MetodoDePagoDR", d["MetodoDePagoDR"])           # "PPD"
            dnode.set("NumParcialidad", str(d["NumParcialidad"]))      # "1", "2", ...
            dnode.set("ImpSaldoAnt", _fmt2(d["ImpSaldoAnt"]))
            dnode.set("ImpPagado", _fmt2(d["ImpPagado"]))
            dnode.set("ImpSaldoInsoluto", _fmt2(d["ImpSaldoInsoluto"]))
            # EquivalenciaDR sólo si moneda DR != moneda del pago
            if d.get("EquivalenciaDR"):
                dnode.set("EquivalenciaDR", d["EquivalenciaDR"])

            # (Opcional) Nodo de impuestos por documento, si aplica (no lo usamos en ejemplo)
            pnode.append(dnode)

        pagos.append(pnode)

    complemento.append(pagos)
    comprobante.append(complemento)

    return comprobante

# ----------------- MAIN: LLENAR DATOS Y FIRMAR -----------------
if __name__ == "__main__":
    # Rutas de tu CSD
    CER_PATH = "CSD_Sucursal_1_EKU9003173C9_20230517_223850.cer"
    KEY_PATH = "CSD_Sucursal_1_EKU9003173C9_20230517_223850.key"
    KEY_PASS = "12345678a"   # usa r"..." si tiene caracteres especiales

    # Asegura XSLT (para cadena original)
    ensure_file(XSLT_LOCAL, SAT_XSLT_URL)

    # Datos de ejemplo (ajústalos a tu operación real)
    datos = {
        "Serie": "PAG",
        "Folio": "1",
        "Fecha": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "Exportacion": "01",
        "LugarExpedicion": "01000",
        "Emisor": {
            "Rfc": "EKU9003173C9",          # CSD de pruebas
            "Nombre": "ESCUELA KEMPER URGATE",
            "RegimenFiscal": "601",
        },
        "Receptor": {
            "Rfc": "XAXX010101000",
            "Nombre": "VENTAS GENERAL",
            "DomicilioFiscalReceptor": "01000",
            "RegimenFiscalReceptor": "616",
        },
        # Complemento de pagos: un pago que liquida parcialidad 1 de una factura
        "Pagos": [
            {
                "FechaPago": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "FormaDePagoP": "03",      # Transferencia electrónica
                "MonedaP": "MXN",
                "Monto": "500.00",
                "DoctosRelacionados": [
                    {
                        "IdDocumento": "11111111-2222-3333-4444-555555555555",  # UUID de la factura PPD
                        "Serie": "FAC",
                        "Folio": "123",
                        "MonedaDR": "MXN",
                        "MetodoDePagoDR": "PPD",
                        "NumParcialidad": 1,
                        "ImpSaldoAnt": "1000.00",
                        "ImpPagado": "500.00",
                        "ImpSaldoInsoluto": "500.00",
                    }
                ],
            }
        ],
    }

    # 1) Cargar NoCertificado y Certificado desde el .cer
    no_cert, cert_b64 = load_cert_info(CER_PATH)

    # 2) Construir el CFDI de Pago 2.0 con NoCertificado/Certificado (sin Sello)
    xml = build_cfdi_pago20_xml(datos, no_cert, cert_b64)

    # 3) Generar Cadena Original (incluye ya el complemento y los atributos del comprobante)
    cadena = cadena_original_from_xml(xml, XSLT_LOCAL)
    # print("CADENA ORIGINAL:\n", cadena)

    # 4) Firmar Cadena con tu .key
    sello_b64 = sign_cadena(KEY_PATH, KEY_PASS, cadena)

    # 5) Insertar Sello
    xml.set("Sello", sello_b64)

    # 6) Guardar XML listo para timbrar en el PAC
    OUT = "pago20_sin_timbrar.xml"
    save_xml(xml, OUT)
    print(f"CFDI Pago 2.0 generado: {OUT}")
