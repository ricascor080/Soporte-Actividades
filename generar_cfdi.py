# -*- coding: utf-8 -*-
import base64
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from lxml import etree
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_der_private_key
from cryptography import x509

NS = {
    "cfdi": "http://www.sat.gob.mx/cfd/4",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
SCHEMA_LOCATION = "http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd"

def _fmt(amount):
    """Formatea con 2 o 6 decimales según corresponda (CFDI)."""
    if isinstance(amount, str):
        return amount
    q = Decimal(str(amount))
    # Por regla general: importes 2 decimales; tasas/cuotas 6
    return format(q.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")

def _fmt6(rate):
    q = Decimal(str(rate))
    return format(q.quantize(Decimal("0.000000"), rounding=ROUND_HALF_UP), "f")

def load_cert_info(cer_path):
    """
    Lee .cer (DER) y retorna (no_certificado_20, certificado_base64) adecuados para CFDI.
    En CSD del SAT el serial trae los 20 dígitos en ASCII embebido.
    """
    with open(cer_path, "rb") as f:
        der = f.read()
    cert = x509.load_der_x509_certificate(der)

    # Serial a hex
    hex_serial = format(cert.serial_number, "x")
    if len(hex_serial) % 2 == 1:
        hex_serial = "0" + hex_serial  # padding par

    no_cert = None
    try:
        # Interpretar como ASCII
        ascii_bytes = bytes.fromhex(hex_serial)
        ascii_text = ascii_bytes.decode("ascii", errors="ignore")
        # Extraer solo dígitos
        digits = "".join(ch for ch in ascii_text if ch.isdigit())
        # Tomar exactamente 20 dígitos (los del final suelen ser los correctos)
        if len(digits) >= 20:
            no_cert = digits[-20:]
        else:
            no_cert = digits.zfill(20)
    except Exception:
        # Fallback: recortar/pad el decimal (menos confiable)
        no_cert = str(cert.serial_number)[-20:].zfill(20)

    cert_b64 = base64.b64encode(der).decode("ascii")
    return no_cert, cert_b64

def sign_cadena_with_key_der(key_der_path, password, cadena):
    """Firma la cadena original con la .key (DER PKCS8, encriptada) y regresa sello Base64."""
    with open(key_der_path, "rb") as f:
        key_der = f.read()
    private_key = load_der_private_key(key_der, password.encode("utf-8"))
    signature = private_key.sign(
        cadena.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode("ascii")

def build_cfdi_xml(data):
    """Construye el Comprobante CFDI 4.0 sin Sello (se inserta al final)."""
    E = etree.Element
    comprobante = E("{%s}Comprobante" % NS["cfdi"], nsmap=NS)

    # Atributos del comprobante (orden no afecta la cadena original)
    attr = {
        "Version": "4.0",
        "Serie": data["Serie"],
        "Folio": data["Folio"],
        "Fecha": data["Fecha"],  # ISO 8601: YYYY-MM-DDTHH:MM:SS
        "Sello": "",  # se llena después
        "FormaPago": data["FormaPago"],
        "NoCertificado": "",  # se llena después
        "Certificado": "",    # se llena después
        "SubTotal": _fmt(data["SubTotal"]),
        "Descuento": _fmt(data.get("Descuento", 0)),
        "Moneda": data["Moneda"],
        "Total": _fmt(data["Total"]),
        "TipoDeComprobante": data["TipoDeComprobante"],
        "Exportacion": data.get("Exportacion", "01"),
        "MetodoPago": data["MetodoPago"],
        "LugarExpedicion": data["LugarExpedicion"],
    }
    for k, v in attr.items():
        if v in ("", None):
            continue
        comprobante.set(k, v)

    # schemaLocation
    comprobante.set("{%s}schemaLocation" % NS["xsi"], SCHEMA_LOCATION)

    # Emisor
    emisor = E("{%s}Emisor" % NS["cfdi"])
    for k, v in data["Emisor"].items():
        emisor.set(k, v)
    comprobante.append(emisor)

    # Receptor
    receptor = E("{%s}Receptor" % NS["cfdi"])
    for k, v in data["Receptor"].items():
        receptor.set(k, v)
    comprobante.append(receptor)

    # Conceptos
    conceptos = E("{%s}Conceptos" % NS["cfdi"])
    for c in data["Conceptos"]:
        concepto = E("{%s}Concepto" % NS["cfdi"])
        for k in ("ClaveProdServ","NoIdentificacion","Cantidad","ClaveUnidad","Descripcion",
                  "ValorUnitario","Importe","Descuento","ObjetoImp"):
            if k in c and c[k] is not None:
                concepto.set(k, _fmt(c[k]) if k in ("ValorUnitario","Importe","Descuento") else str(c[k]))

        # Impuestos por concepto
        if "Impuestos" in c and "Traslados" in c["Impuestos"]:
            imp = E("{%s}Impuestos" % NS["cfdi"])
            traslados = E("{%s}Traslados" % NS["cfdi"])
            for t in c["Impuestos"]["Traslados"]:
                traslado = E("{%s}Traslado" % NS["cfdi"])
                traslado.set("Base", _fmt(t["Base"]))
                traslado.set("Impuesto", t["Impuesto"])      # 002 = IVA
                traslado.set("TipoFactor", t["TipoFactor"])  # Tasa
                traslado.set("TasaOCuota", _fmt6(t["TasaOCuota"]))
                traslado.set("Importe", _fmt(t["Importe"]))
                traslados.append(traslado)
            imp.append(traslados)
            concepto.append(imp)

        conceptos.append(concepto)
    comprobante.append(conceptos)

    # Impuestos (totales)
    if "Impuestos" in data:
        imp_t = E("{%s}Impuestos" % NS["cfdi"])
        if "TotalImpuestosTrasladados" in data["Impuestos"]:
            imp_t.set("TotalImpuestosTrasladados", _fmt(data["Impuestos"]["TotalImpuestosTrasladados"]))
        if "Traslados" in data["Impuestos"]:
            traslados = E("{%s}Traslados" % NS["cfdi"])
            for t in data["Impuestos"]["Traslados"]:
                traslado = E("{%s}Traslado" % NS["cfdi"])
                traslado.set("Base", _fmt(t["Base"]))
                traslado.set("Impuesto", t["Impuesto"])
                traslado.set("TipoFactor", t["TipoFactor"])
                traslado.set("TasaOCuota", _fmt6(t["TasaOCuota"]))
                traslado.set("Importe", _fmt(t["Importe"]))
                traslados.append(traslado)
            imp_t.append(traslados)
        comprobante.append(imp_t)

    return comprobante

def cadena_original_from_xml(xml_tree, xslt_path):
    xslt = etree.parse(xslt_path)
    transform = etree.XSLT(xslt)
    result = transform(xml_tree)
    return str(result)

def insert_sello_y_cert(xml_tree, sello_b64, cert_b64, no_cert):
    xml_tree.set("Sello", sello_b64)
    xml_tree.set("Certificado", cert_b64)
    xml_tree.set("NoCertificado", no_cert)

def save_xml(xml_tree, path):
    etree.ElementTree(xml_tree).write(
        path, encoding="UTF-8", xml_declaration=True, pretty_print=True
    )

def validar_xml_con_xsd(xml_path, xsd_path):
    """Valida un XML contra un XSD local. Retorna True si es válido, False si no. Imprime errores si existen."""
    with open(xsd_path, 'rb') as f:
        schema_doc = etree.parse(f)
    schema = etree.XMLSchema(schema_doc)
    xml_doc = etree.parse(xml_path)
    valido = schema.validate(xml_doc)
    if not valido:
        print("Errores de validación:")
        for error in schema.error_log:
            print(f"Línea {error.line}: {error.message}")
    return valido

# ---------- EJEMPLO DE USO ----------
if __name__ == "__main__":
    # Rutas a tus llaves/certificados y xslt
    CER_PATH = "CSD_Sucursal_1_EKU9003173C9_20230517_223850.cer"
    KEY_PATH = "CSD_Sucursal_1_EKU9003173C9_20230517_223850.key"
    KEY_PASS = "12345678a"  # contraseña del CSD
    XSLT_PATH = "cadenaoriginal_4_0.xslt"

    datos = {
    "Serie": "FA",
    "Folio": "1001",
    "Fecha": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    "FormaPago": "01",   # Efectivo
    "SubTotal": "1000.00",
    "Descuento": "0.00",
    "Moneda": "MXN",
    "Total": "1160.00",  # 1000 + IVA 160
    "TipoDeComprobante": "I",
    "Exportacion": "01",
    "MetodoPago": "PUE",
    "LugarExpedicion": "01000",
    "Emisor": {
        "Rfc": "EKU9003173C9",                # RFC de emisor prueba
        "Nombre": "ESCUELA KEMPER URGATE",
        "RegimenFiscal": "601",
    },
    "Receptor": {
        "Rfc": "MASO451221PM4",                # RFC de receptor de prueba válido
        "Nombre": "MARIA OLIVIA MARTINEZ SAGAZ",
        "DomicilioFiscalReceptor": "01000",
        "RegimenFiscalReceptor": "601",
        "UsoCFDI": "CP01",                     # Adquisición de mercancías
    },
    "Conceptos": [
        {
            "ClaveProdServ": "01010101",
            "NoIdentificacion": "001",
            "Cantidad": "1",
            "ClaveUnidad": "ACT",
            "Descripcion": "Venta de producto de prueba",
            "ValorUnitario": "1000.00",
            "Importe": "1000.00",
            "ObjetoImp": "02",                 # Sí objeto de impuesto
            "Impuestos": {
                "Traslados": [
                    {
                        "Base": "1000.00",
                        "Impuesto": "002",     # IVA
                        "TipoFactor": "Tasa",
                        "TasaOCuota": "0.160000",
                        "Importe": "160.00",
                    }
                ]
            },
        }
    ],
    "Impuestos": {
        "TotalImpuestosTrasladados": "160.00",
        "Traslados": [
            {
                "Base": "1000.00",
                "Impuesto": "002",
                "TipoFactor": "Tasa",
                "TasaOCuota": "0.160000",
                "Importe": "160.00",
            }
        ],
    },
}


    # 0) Cargar NoCertificado y Certificado ANTES de la cadena
    no_cert, cert_b64 = load_cert_info(CER_PATH)

    # 1) Construir XML sin sello (pero con NoCertificado y Certificado ya puestos)
    xml = build_cfdi_xml(datos)
    insert_sello_y_cert(xml, sello_b64="", cert_b64=cert_b64, no_cert=no_cert)

    # 2) Cadena Original (ya incluye NoCertificado y Certificado)
    cadena = cadena_original_from_xml(xml, XSLT_PATH)
    # print("CADENA ORIGINAL:\n", cadena)

    # 3) Sello con tu .key
    sello_b64 = sign_cadena_with_key_der(KEY_PATH, KEY_PASS, cadena)

    # 4) Insertar Sello
    xml.set("Sello", sello_b64)

    # 5) Guardar XML listo para timbrar
    save_xml(xml, "cfdi40_ejemplo.xml")
    print("CFDI 4.0 generado: cfdi40_ejemplo.xml")

    # 6) Validar contra XSD local
    XSD_PATH = "cfdv40.xsd"
    es_valido = validar_xml_con_xsd("cfdi40_ejemplo.xml", XSD_PATH)
    print("¿XML válido contra XSD local?", es_valido)
