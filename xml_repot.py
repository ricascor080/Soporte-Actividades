# -*- coding: utf-8 -*-

from zeep import Client
import logging
import base64
from lxml import etree
from zeep.plugins import HistoryPlugin


username = 'ricascor080@gmail.com' # Usuario de Finkok
password = 'Ricas002385.' # Contraseña de Finkok

rfc= 'EKU9003173C9'
dateFrom = '2025-08-01T00:00:00'
dateTo = '2025-08-19T00:00:00'
invoice = 'I'

url = "https://demo-facturacion.finkok.com/servicios/soap/utilities.wsdl"
history = HistoryPlugin()
client = Client(wsdl = url, plugins = [history])

response = client.service.report_uuid(username,password,rfc,dateFrom,dateTo)
print(response)

if response.invoices is None:
    print ("No se encontraron comprobantes")
else:
    uuids = response.invoices.ReportUUID
    try:
       size=len(uuids)
       count=0
       for uuid in uuids:
           responsexml=client.service.get_xml(username,password,uuid.uuid,rfc, invoice)
           xml = responsexml.xml
           name = (str(uuid.uuid)+"-"+str(uuid.date)).replace(" ","")
           xmlfile = open(name+'reporte_0000.xml','w')
           xmlfile.write(xml)
           count +=1
           #percent=(count*10)/size
           print (str(count))
    except Exception as e:
        print(str(e))

# Get SOAP Request
request = etree.tostring(history.last_sent["envelope"])
req_file = open('request_xmls.xml', 'w')
req_file.write(request.decode("UTF-8") )
req_file.close()

# Get SOAP Response
response = etree.tostring(history.last_received["envelope"])
res_file = open('response_xmls.xml', 'w')
res_file.write(response.decode("UTF-8") )
res_file.close()