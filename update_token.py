#!/usr/bin/python
from zeep import Client
from zeep.plugins import HistoryPlugin
from lxml import etree
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger('zeep.client').setLevel(logging.DEBUG)
logging.getLogger('zeep.transport').setLevel(logging.DEBUG)
logging.getLogger('zeep.xsd.schema').setLevel(logging.DEBUG)
logging.getLogger('zeep.wsdl').setLevel(logging.DEBUG)

username = 'ricascor080@gmail.com'
password = 'Ricas002385.'
token = 'Inova'  # Nombre del token a actualizar
status = '0'

# === Ruta base donde quieres guardar ===
BASE = Path("/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/token")
BASE.mkdir(parents=True, exist_ok=True)  # crea la carpeta si no existe

# Conexión
url = "https://demo-facturacion.finkok.com/servicios/soap/utilities.wsdl"
history = HistoryPlugin()
client = Client(wsdl=url, plugins=[history])

# Llamada
resultado = client.service.update_token(username, password, token, status)
print(resultado)

# Guarda el resultado textual
with open(BASE / "update_token.txt", "w", encoding="utf-8") as f:
    f.write(str(resultado))

# Guarda SOAP Request (si existe)
if history.last_sent:
    request_xml = etree.tostring(history.last_sent["envelope"], encoding="utf-8", pretty_print=True)
    with open(BASE / "requestupdate.xml", "wb") as f:
        f.write(request_xml)

# Guarda SOAP Response (si existe)
if history.last_received:
    response_xml = etree.tostring(history.last_received["envelope"], encoding="utf-8", pretty_print=True)
    with open(BASE / "responseupdate.xml", "wb") as f:
        f.write(response_xml)

print(f"Archivos guardados en: {BASE}")
