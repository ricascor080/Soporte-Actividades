from decimal import Decimal, ROUND_HALF_UP
from zeep import Client, Settings
from zeep.plugins import HistoryPlugin
from lxml import etree
from pathlib import Path

USERNAME = "ricascor080@gmail.com"
PASSWORD = "Ricas002385."

UUID = "122D648B-CD0B-5D5D-AEA4-FF8B0AD93394"
RFC_EMISOR = "EKU9003173C9"
RFC_RECEPTOR = "AABF800614HI0"
TOTAL = "0"              

WSDL_CANCEL = "https://demo-facturacion.finkok.com/servicios/soap/cancel.wsdl"

def to_6(x):
    return str(Decimal(x).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))

def save_envelopes(history: HistoryPlugin, prefix: str = "sat_status"):
    outdir = Path("soap_traces")
    outdir.mkdir(exist_ok=True)
    if history.last_sent:
        req_xml = etree.tostring(
            history.last_sent["envelope"],
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )
        (outdir / f"{prefix}_requestCASO2.xml").write_bytes(req_xml)
        (outdir / f"{prefix}_request_headers.txt").write_text(
            str(history.last_sent.get("http_headers", "")), encoding="utf-8"
        )
    if history.last_received:
        res_xml = etree.tostring(
            history.last_received["envelope"],
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
        )
        (outdir / f"{prefix}_responseCASO2.xml").write_bytes(res_xml)
        (outdir / f"{prefix}_response_headers.txt").write_text(
            str(history.last_received.get("http_headers", "")), encoding="utf-8"
        )

history = HistoryPlugin()
client = Client(
    WSDL_CANCEL,
    settings=Settings(strict=False, xml_huge_tree=True),
    plugins=[history],
)

# get_sat_status(username, password, taxpayer_id, rtaxpayer_id, uuid, total)
resp = client.service.get_sat_status(
    USERNAME, PASSWORD, RFC_EMISOR, RFC_RECEPTOR, UUID, to_6(TOTAL)
)
print(resp)

# Guarda request/response del ÚLTIMO llamado:
save_envelopes(history, prefix="sat_status")
print("Guardados en ./soap_traces/: sat_status_requestAcep.xml / sat_status_responseAcep.xml")
