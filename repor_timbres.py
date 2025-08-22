#!/usr/bin/python
# -*- coding: utf-8 -*-

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

username = 'al19020225@itsa.edu.mx' # Usuario de Finkok
password = '#/Hansol1' # Password de Finkok

rfc= 'EKU9003173C9' # RFC Emisor del cual desea realizar el reporte

#dateFrom = '2025-08-11T19:58:18' #2025-08-11 19:58:18'
#dateTo = '2025-08-19T15:30:22' #2025-08-19 15:30:22
dateFrom = '2025-08-04T00:00:00'
dateTo = '2025-08-20T00:00:00'

invoice_type = 'I' # Tipo de factura Tipos ('I' Ingreso, 'R' Retenciones)

url = "https://demo-facturacion.finkok.com/servicios/soap/utilities.wsdl" # URL del web service de Utilerias
history = HistoryPlugin()
client = Client(wsdl = url, plugins = [history]) # Conexión al webservice
respuesta = client.service.report_total(username, password, rfc,dateFrom, dateTo, invoice_type) # Envio de parametros al web service
print(respuesta)

archivo = open("Report_total.xml","w") # Creación del archivo .xml

i= 0
while i < 1:
    archivo.write("Total de timbres: "+str(respuesta.result.ReportTotal[i].total)+"\n") # Obtención del parámetro total (Total de timbrado)
    archivo.write("RFC: "+str(respuesta.result.ReportTotal[i].taxpayer_id)+"\n\n") # Obtención del parámetro taxpayer_id (RFC emisor)
    i = i + 1

archivo.close() # Cerrar archivo .xml

# Get SOAP Request
request = etree.tostring(history.last_sent["envelope"])
req_file = open('request_Total_Tim.xml', 'w')
req_file.write(request.decode("UTF-8") )
req_file.close()

# Get SOAP Response
response = etree.tostring(history.last_received["envelope"])
res_file = open('response_Total_Tim.xml', 'w')
res_file.write(response.decode("UTF-8") )
res_file.close()