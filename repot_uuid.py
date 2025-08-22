#!/usr/bin/python
from suds.client import Client
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
logging.getLogger('suds.transport').setLevel(logging.DEBUG)
logging.getLogger('suds.xsd.schema').setLevel(logging.DEBUG)
logging.getLogger('suds.wsdl').setLevel(logging.DEBUG)

username = 'ricascor080@gmail.com' # Usuario de Finkok
password = 'Ricas002385.' # Password de Finkok
rfc= 'EKU9003173C9' # RFC Emisor del cual desea realizar el reporte
desde = '2025-08-01T00:00:00' # Fecha y hora inicial de la busqueda
hasta = '2025-09-01T00:00:00' # Fecha y hora Final de la busqueda
invoice_type = 'I'

url = "https://demo-facturacion.finkok.com/servicios/soap/utilities.wsdl" # URL del web service de Utilerias
client = Client(url,cache=None) # Conexión al webservice
respuesta = client.service.report_uuid(username,password,rfc,desde,hasta,invoice_type) # Envio de parametros al web service
uuids = respuesta.invoices.ReportUUID # Respuesta del web service
size=len(uuids) # Se contabiliza los uuids obtenidos de la respuesta del web service

archivo = open("Report_uuid___.xml","w") # Creación del archivo .xml

i= 0
while i < size:
    archivo.write("FECHA: "+str(respuesta.invoices.ReportUUID[i].date)+"\n") # Obtención del parámetro date (Fecha de timbrado)
    archivo.write("UUID: "+str(respuesta.invoices.ReportUUID[i].uuid)+"\n\n") # Obtención del parámetro uuid
    i = i + 1

archivo.close() # Cerrar archivo .xml