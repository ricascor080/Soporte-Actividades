#!/usr/bin/python

from suds.client import Client
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
logging.getLogger('suds.transport').setLevel(logging.DEBUG)
logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

username = 'ricascor080@gmail.com' # Usuario de Finkok
password = 'Ricas002385.' # Contraseña de Finkok
name='Inova'  #Nombre con el que aparecerá en el panel administrativo de Tokens
token_username='Inova' #Nombre del usuario
taxpayer_id='IVD920810GU2' #RFC al que se le asignara el Token (Nota: sino se asigna un RFC se creara un Token global )
status='true' #Estatus del token

# Conexión al web service de Utilities (add_token)
url = "https://demo-facturacion.finkok.com/servicios/soap/utilities.wsdl"
client = Client(url, cache=None)

print (client.service.add_token(username, password,name,token_username,taxpayer_id,status))

# Get SOAP Request
last_request = client.last_sent()
req_file = open("/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/token/Request.xml", "w")
req_file.write(str(last_request))
req_file.close()

# Get SOAP Response
last_response = client.last_received()
res_file = open("/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/token/Response.xml", "w")
res_file.write(str(last_response))
res_file.close()