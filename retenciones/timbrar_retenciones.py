# timbrar_retenciones.py
# pip install zeep lxml

from lxml import etree
from zeep import Client
from zeep.transports import Transport
from zeep.plugins import HistoryPlugin

USERNAME = "ricascor080@gmail.com"
PASSWORD = "Ricas002385."
WSDL = "https://demo-facturacion.finkok.com/servicios/soap/retentions.wsdl"

XML_PATH = "retenciones20_sin_timbrar.xml"

def read_xml(path):
    with open(path, "rb") as f:
        return f.read()

def preview_receptor(xml_bytes):
    try:
        doc = etree.fromstring(xml_bytes)
        ns = {"ret": "http://www.sat.gob.mx/esquemas/retencionpago/2"}
        nodo = doc.xpath("//ret:Receptor/ret:Nacional", namespaces=ns)
        if nodo:
            print("Prévia Receptor => RfcR=", nodo[0].get("RfcR"),
                  " NomDenRazSocR=", nodo[0].get("NomDenRazSocR"))
    except Exception as e:
        print("No pude previsualizar el XML:", e)

def main():
    xml_bytes = read_xml(XML_PATH)
    preview_receptor(xml_bytes)

    hist = HistoryPlugin()
    client = Client(WSDL, transport=Transport(), plugins=[hist])

    params = {
        "xml": xml_bytes,        # EN BRUTO (no lo codifiques a base64)
        "username": USERNAME,
        "password": PASSWORD,
    }

    try:
        resp = client.service.stamp(**params)
    except Exception as e:
        print("\n--- SOAP Request ---")
        if hist.last_sent:
            print(hist.last_sent["envelope"].decode("utf-8", errors="ignore"))
        print("\n--- SOAP Response ---")
        if hist.last_received:
            print(hist.last_received["envelope"].decode("utf-8", errors="ignore"))
        print("\nError:", e)
        return

    sr = getattr(resp, "stampResult", resp)
    print("\n--- Resultado ---")
    print({
        "UUID": getattr(sr, "UUID", None),
        "CodEstatus": getattr(sr, "CodEstatus", None),
        "Fecha": getattr(sr, "Fecha", None),
    })

    if getattr(sr, "xml", None):
        with open("retenciones20_timbrado.xml", "wb") as f:
            f.write(sr.xml)
        print("✅ Guardado: retenciones20_timbrado.xml")

    incs = getattr(sr, "Incidencias", None)
    if incs and getattr(incs, "Incidencia", None):
        incidencias = incs.Incidencia
        if not isinstance(incidencias, list):
            incidencias = [incidencias]
        for i in incidencias:
            print(f"⚠ Incidencia: {getattr(i, 'CodigoError', '')} - {getattr(i, 'MensajeIncidencia', '')}")
            if getattr(i, "ExtraInfo", None):
                print("   ExtraInfo:", i.ExtraInfo)

if __name__ == "__main__":
    main()
