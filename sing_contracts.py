#!/usr/bin/python
from suds.client import Client
import logging
import base64

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
logging.getLogger('suds.transport').setLevel(logging.DEBUG)
logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

snid = "SN08254651"
privacy_path = "/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/Manifiesto/privacidad_signature.xml"
with open(privacy_path, "rb") as f:
    privacy_file = base64.b64encode(f.read()).decode("utf-8")

contract_path = "/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/Manifiesto/contract_signature.xml"
with open(contract_path, "rb") as f:
    contract_file = base64.b64encode(f.read()).decode("utf-8")
    
url = "https://manifiesto.cfdiquadrum.com.mx:8008/servicios/soap/firmar.wsdl"
client = Client(url, cache=None)
cont = client.service.sign_contract(snid, privacy_file, contract_file)

last_request = client.last_sent()
req_file = open('/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/Manifiesto/FIRMArequest.xml','w')
req_file.write(str(last_request))
req_file.close()

last_response = client.last_received()
res_file = open('/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/Manifiesto/FIRMAresponse.xml', 'w')
res_file.write(str(last_response))
res_file.close()