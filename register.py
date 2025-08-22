from zeep import Client
import logging
import base64
from lxml import etree
from zeep.plugins import HistoryPlugin

logging.basicConfig(level=logging.INFO)
logging.getLogger('zeep.client').setLevel(logging.DEBUG)
logging.getLogger('zeep.transport').setLevel(logging.DEBUG)
logging.getLogger('zeep.xsd.schema').setLevel(logging.DEBUG)
logging.getLogger('zeep.wsdl').setLevel(logging.DEBUG)

# Username y Password de Finkok
username = "ricascor080@gmail.com"
password = "Ricas002385."

RFC = 'IIA040805DZ4'
type_user = 'O'
coupon = ''
added = ''

# Read the x509 certificate file on PEM format and encode it on base64
cer_path = "Certificado.cer"
file = open(cer_path, "rb")
cer = (file.read())


key_path = "llave.key"
file = open(key_path, "rb")
key = (file.read())

passphrase = '12345678a'

url = "https://demo-facturacion.finkok.com/servicios/soap/registration.wsdl"
history = HistoryPlugin()
client = Client(wsdl = url, plugins = [history])

response = client.service.add(username,password,RFC, type_user, '', '',cer, key, passphrase)
print(response)

archivo = open("add.txt", "w")
archivo.write(str(response))
archivo.close()

# Get SOAP Request
request = etree.tostring(history.last_sent["envelope"])
req_file = open('request.xml', 'w')
req_file.write(request.decode("UTF-8"))
req_file.close()

# Get SOAP Response
response = etree.tostring(history.last_received["envelope"])
res_file = open('response.xml', 'w')
res_file.write(response.decode("UTF-8"))
res_file.close()