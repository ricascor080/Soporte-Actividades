#!/usr/bin/python
# -*- coding: utf-8 -*-

from zeep import Client
from zeep.plugins import HistoryPlugin
import logging
from lxml import etree

# --- Logging (opcional: útil para depurar) ---
logging.basicConfig(level=logging.INFO)
logging.getLogger('zeep.client').setLevel(logging.DEBUG)
logging.getLogger('zeep.transport').setLevel(logging.DEBUG)
logging.getLogger('zeep.xsd.schema').setLevel(logging.DEBUG)
logging.getLogger('zeep.wsdl').setLevel(logging.DEBUG)

# --- Credenciales Finkok ---
username = 'ricascor080@gmail.com'     # <-- tu usuario/correo Finkok (demo o prod)
password = 'Ricas002385.'            # <-- tu contraseña

# --- Archivo XML base (RETENCIONES 2.0, sin Sello/Cert/NumCert) ---
invoice_path = "retencion_extran.xml"

# --- Plugin para guardar request/response SOAP ---
history = HistoryPlugin()

# --- WSDL de RETENCIONES (usar sign_stamp) ---
# Demo: https://demo-facturacion.finkok.com/servicios/soap/retentions.wsdl
url = "https://demo-facturacion.finkok.com/servicios/soap/retentions.wsdl"
client = Client(wsdl=url, plugins=[history])

# --- Leer XML tal cual (bytes) ---
with open(invoice_path, "rb") as f:
    xml_bytes = f.read()

# IMPORTANTE:
# No lo codifiques tú a base64; Zeep lo hace automáticamente para tipos base64Binary.

# --- Consumir sign_stamp (RETENCIONES) ---
contenido = client.service.sign_stamp(xml_bytes, username, password)

# 'contenido' puede traer:
# - xml (timbrado) si todo salió bien
# - Incidencias si hubo errores de validación

# --- Guardar XML timbrado (si existe) ---
timbrado_path = "stamp_retenciones.xml"
if hasattr(contenido, "xml") and contenido.xml:
    # contenido.xml puede ser str o bytes
    xml_timbrado = contenido.xml if isinstance(contenido.xml, bytes) else contenido.xml.encode("utf-8")
    with open(timbrado_path, "wb") as archivo:
        archivo.write(xml_timbrado)
    print("✅ Timbrado guardado en:", timbrado_path)

    # Intentar extraer UUID del TimbreFiscalDigital
    try:
        doc = etree.fromstring(xml_timbrado)
        ns = {
            "ret": "http://www.sat.gob.mx/esquemas/retencionpago/2",
            "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital"
        }
        uuid = doc.xpath("//ret:Complemento/tfd:TimbreFiscalDigital/@UUID", namespaces=ns)
        if uuid:
            print("UUID:", uuid[0])
        else:
            print("UUID no encontrado en el complemento (revisa response.xml).")
    except Exception as e:
        print("No se pudo leer el UUID:", e)
else:
    print("❌ No se obtuvo XML timbrado.")
    # Imprimir incidencias si vienen
    if hasattr(contenido, "Incidencias") and contenido.Incidencias:
        try:
            incs = contenido.Incidencias.Incidencia
            if isinstance(incs, list):
                for i in incs:
                    print(f"[Incidencia] CodigoError={getattr(i,'CodigoError',None)} Mensaje={getattr(i,'MensajeIncidencia',None)}")
            else:
                print(f"[Incidencia] CodigoError={getattr(incs,'CodigoError',None)} Mensaje={getattr(incs,'MensajeIncidencia',None)}")
        except Exception as e:
            print("Incidencias (sin parsear):", contenido.Incidencias, "Error:", e)
    else:
        print(contenido)

# --- Guardar SOAP Request/Response para auditoría ---
try:
    request_env = etree.tostring(history.last_sent["envelope"])
    with open('request.xml', 'wb') as req_file:
        req_file.write(request_env)
    response_env = etree.tostring(history.last_received["envelope"])
    with open('response.xml', 'wb') as res_file:
        res_file.write(response_env)
    print("📝 request.xml y response.xml guardados.")
except Exception as e:
    print("No se pudieron guardar request/response SOAP:", e)
