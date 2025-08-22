# -*- coding: utf-8 -*-
from lxml import etree
from decimal import Decimal, ROUND_HALF_UP
import os, pathlib, urllib.request, hashlib

NS = {
    "ret": "http://www.sat.gob.mx/esquemas/retencionpago/2",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
SCHEMA_LOCATION = (
    "http://www.sat.gob.mx/esquemas/retencionpago/2 "
    "http://www.sat.gob.mx/esquemas/retencionpago/2/retencionpagov2.xsd"
)

XSD_MAIN_URL  = "http://www.sat.gob.mx/esquemas/retencionpago/2/retencionpagov2.xsd"
XSD_MAIN_FILE = "retencionpagov2.xsd"
XSD_CACHE_DIR = pathlib.Path("xsd_cache")
XSD_CACHE_DIR.mkdir(exist_ok=True)

def fmt2(val):
    q = Decimal(str(val))
    return str(q.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP))

def download_if_missing(url: str) -> pathlib.Path:
    ext = ".xsd" if url.lower().endswith(".xsd") else ".xsd"
    name = hashlib.sha1(url.encode("utf-8")).hexdigest() + ext
    local_path = XSD_CACHE_DIR / name
    if not local_path.exists():
        print(f"Descargando: {url}")
        urllib.request.urlretrieve(url, local_path)
        print(f"Guardado: {local_path}")
    return local_path

class HttpToCacheResolver(etree.Resolver):
    def resolve(self, system_url, public_id, context):
        if system_url.startswith(("http://","https://")):
            local = download_if_missing(system_url)
            return self.resolve_filename(str(local), context)
        if os.path.exists(system_url):
            return self.resolve_filename(system_url, context)
        return None

def build_xml_extranjero(base_para_validar=True):
    """
    base_para_validar=True  -> incluye Sello/NoCertificado/Certificado (placeholders) para pasar XSD.
    base_para_validar=False -> quita esos atributos para enviar por sign_stamp.
    """
    Ret = etree.Element(
        etree.QName(NS["ret"], "Retenciones"),
        nsmap={"retenciones": NS["ret"], "xsi": NS["xsi"]},
    )
    Ret.set("Version", "2.0")
    Ret.set("FechaExp", "2025-08-12T00:04:17")
    Ret.set("CveRetenc", "01")
    Ret.set("LugarExpRetenc", "01000")
    Ret.set("FolioInt", "R0001")
    Ret.set(etree.QName(NS["xsi"], "schemaLocation"), SCHEMA_LOCATION)

    if base_para_validar:
        # Placeholders para satisfacer XSD (cadena base64 mínima y número)
        Ret.set("Sello", "AA==")
        Ret.set("NoCertificado", "30001000000500003416")
        Ret.set("Certificado", "AA==")

    emisor = etree.SubElement(Ret, etree.QName(NS["ret"], "Emisor"))
    emisor.set("RfcE", "EKU9003173C9")
    emisor.set("NomDenRazSocE", "ESCUELA KEMPER URGATE")
    emisor.set("RegimenFiscalE", "601")

    receptor = etree.SubElement(Ret, etree.QName(NS["ret"], "Receptor"))
    receptor.set("Nacionalidad", "Extranjero")

    extr = etree.SubElement(receptor, etree.QName(NS["ret"], "Extranjero"))
    extr.set("NomDenRazSocR", "JOHN DOE INC.")
    extr.set("NumRegIdTrib", "US123456789")

    per = etree.SubElement(Ret, etree.QName(NS["ret"], "Periodo"))
    per.set("MesIni", "01")
    per.set("MesFin", "01")
    per.set("Ejercicio", "2025")

    tot = etree.SubElement(Ret, etree.QName(NS["ret"], "Totales"))
    tot.set("MontoTotOperacion", fmt2("1000.00"))
    tot.set("MontoTotGrav", fmt2("1000.00"))
    tot.set("MontoTotExent", fmt2("0.00"))
    tot.set("MontoTotRet", fmt2("100.00"))

    imp = etree.SubElement(tot, etree.QName(NS["ret"], "ImpRetenidos"))
    imp.set("BaseRet", fmt2("1000.00"))
    imp.set("ImpuestoRet", "001")
    imp.set("MontoRet", fmt2("100.00"))
    imp.set("TipoPagoRet", "01")

    return etree.ElementTree(Ret)

def business_checks(xml_tree):
    root = xml_tree.getroot()
    ns = {"ret": NS["ret"]}

    ext = root.xpath("//ret:Receptor/ret:Extranjero", namespaces=ns)
    if not ext:
        raise ValueError("Falta ret:Extranjero dentro de ret:Receptor.")
    ext = ext[0]
    for a in ("NomDenRazSocR", "NumRegIdTrib"):
        if not ext.get(a):
            raise ValueError(f"Falta atributo obligatorio en Extranjero: {a}")

    tot = root.find(".//ret:Totales", namespaces=ns)
    if tot is None:
        raise ValueError("Falta ret:Totales.")

    # 2 decimales
    for attr in ("MontoTotOperacion", "MontoTotGrav", "MontoTotExent", "MontoTotRet"):
        val = tot.get(attr)
        if val is None:
            raise ValueError(f"Falta atributo {attr} en Totales.")
        if "." in val and len(val.split(".")[1]) > 2:
            raise ValueError(f"{attr} debe tener como máximo 2 decimales.")

    from decimal import Decimal
    suma = Decimal("0.00")
    for i in root.findall(".//ret:Totales/ret:ImpRetenidos", namespaces=ns):
        monto = i.get("MontoRet")
        if monto is None:
            raise ValueError("Falta MontoRet en un ret:ImpRetenidos.")
        if "." in monto and len(monto.split(".")[1]) > 2:
            raise ValueError("MontoRet debe tener como máximo 2 decimales.")
        suma += Decimal(monto)

    if suma.quantize(Decimal("0.00")) != Decimal(tot.get("MontoTotRet")).quantize(Decimal("0.00")):
        raise ValueError(f"Mismatch MontoTotRet ({tot.get('MontoTotRet')}) vs suma(MontoRet) ({suma}).")

def validate_xsd_with_remote_imports(xml_tree):
    if not pathlib.Path(XSD_MAIN_FILE).exists():
        print(f"Descargando XSD principal: {XSD_MAIN_URL}")
        urllib.request.urlretrieve(XSD_MAIN_URL, XSD_MAIN_FILE)
        print(f"Guardado: {XSD_MAIN_FILE}")

    parser = etree.XMLParser()
    parser.resolvers.add(HttpToCacheResolver())

    with open(XSD_MAIN_FILE, "rb") as f:
        schema_doc = etree.parse(f, parser=parser)

    schema = etree.XMLSchema(schema_doc)

    if not schema.validate(xml_tree):
        errors = "\n".join(f"L{e.line}: {e.message}" for e in schema.error_log)
        raise ValueError("Validación XSD falló:\n" + errors)

def save_xml(tree, path):
    data = etree.tostring(tree, encoding="UTF-8", xml_declaration=True, pretty_print=True)
    with open(path, "wb") as f:
        f.write(data)

if __name__ == "__main__":
    # 1) Construye XML con placeholders (para VALIDAR)
    tree_validar = build_xml_extranjero(base_para_validar=True)
    business_checks(tree_validar)
    validate_xsd_with_remote_imports(tree_validar)
    save_xml(tree_validar, "retenciones20_validado_estricto.xml")
    print("✅ Generado y validado: retenciones20_validado_estricto.xml")

    # 2) Construye XML para ENVIAR por sign_stamp (sin Sello/NoCertificado/Certificado)
    tree_send = build_xml_extranjero(base_para_validar=False)
    # (No intentes validarlo contra XSD: esos 3 atributos son requeridos por el XSD)
    save_xml(tree_send, "retenciones20_para_sign_stamp.xml")
    print("📦 Generado para sign_stamp (sin sello/cert): retenciones20_para_sign_stamp.xml")
