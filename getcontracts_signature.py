#!/usr/bin/python
from suds.client import Client
import logging
import base64
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
logging.getLogger('suds.transport').setLevel(logging.DEBUG)
logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

snid = "SN08254651"
name = "ESCUELA KEMPER URGATE" #nombre del emisor
taxpayer_id = "EKU9003173C9" #RFC Emisor
address = "Guerrero"
email = "eku@gmail.com"

cer_path = Path("/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/FIEL_EKU/cer.pem")
with open(cer_path, "rb") as f:
    cer_b64 = base64.b64encode(f.read()).decode("utf-8")




key_path = "/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/FIEL_EKU/Fiel.pem"
with open(key_path, "rb") as f:
    key = base64.b64encode(f.read()).decode("utf-8")

print("CER en Base64:\n", cer_b64[:120], "...")  # Solo primeros 120 chars
print("KEY en Base64:\n", key[:120], "...")
url = "https://manifiesto.cfdiquadrum.com.mx:8008/servicios/soap/firmar.wsdl"
client = Client(url, cache=None)
cont = client.service.get_contracts_signature(snid,name,taxpayer_id,address,email,cer_b64,key)

last_request = client.last_sent()
req_file = open('/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/Manifiesto/Request_xmlsignature.xml','w')
req_file.write(str(last_request))
req_file.close()

last_response = client.last_received()
res_file = open('/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/Manifiesto/Response_xmlsignature.xml', 'w')
res_file.write(str(last_response))
res_file.close()