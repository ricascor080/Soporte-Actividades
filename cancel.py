#!/usr/bin/python
# -*- coding: utf-8 -*-

from suds.client import Client
import logging
import base64

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)

def encode_file_to_base64(filepath):
    """Lee un archivo en modo binario y lo codifica en Base64."""
    try:
        with open(filepath, "rb") as file:
            file_content = file.read()
            encoded_content = base64.b64encode(file_content)
            return encoded_content.decode('utf-8')
    except FileNotFoundError:
        print(f"Error: El archivo no fue encontrado en la ruta: {filepath}")
        return None
    except Exception as e:
        print(f"Ocurrió un error al leer el archivo: {e}")
        return None

username = 'ricascor080@gmail.com' # El usuario proporcionado por la plataforma Finkok
password = 'Ricas002385.' # Contraseña proporcionada por la plataforma Finkok
taxpayer_id = 'EKU9003173C9' # El RFC del Emisor

# --- MODIFICADO: Apuntando a los nuevos archivos .pem ---
cer_file = encode_file_to_base64("/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/cer.pem")
key_file = encode_file_to_base64("/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/key.pem")

# Si por alguna razón el archivo no se pudo leer, salimos del script
if not cer_file or not key_file:
    exit()
# Fin de la sección modificada
# ---------------------------------------------

url = "https://demo-facturacion.finkok.com/servicios/soap/cancel.wsdl"
client = Client(url,cache=None)

# IMPORTANTE: Con el motivo '02', el campo FolioSustitucion debe ser eliminado o nulo.
# Si lo dejas, puede causar un error de la API.
invoices_obj = client.factory.create("ns0:UUID")
invoices_obj._UUID='122D648B-CD0B-5D5D-AEA4-FF8B0AD93394'
# invoices_obj._FolioSustitucion='6E50FDCF-34EC-449E-BA3B-4844F4EA678A'  <-- Esta línea DEBE eliminarse
invoices_obj._Motivo='02'
UUIDS_list = client.factory.create("ns0:UUIDArray")

UUIDS_list.UUID.append(invoices_obj)

try:
    result = client.service.cancel(UUIDS_list, username, password, taxpayer_id, cer_file, key_file)
    print("Solicitud enviada con éxito. Verifique el resultado:")
    print(result)
    
    last_request = client.last_sent()
    req_file = open('/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/cancel_scrip/request.xml', 'w')
    req_file.write(str(last_request))
    req_file.close()

    last_response = client.last_received()
    res_file = open('/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/cancel_scrip/response.xml', 'w')
    res_file.write(str(last_response))
    res_file.close()
    
except Exception as e:
    print("Ocurrió un error al intentar la cancelación:")
    print(e)
    # También podemos imprimir la última respuesta para ver más detalles del error de la API
    last_response = client.last_received()
    if last_response:
        print("\nÚltima respuesta del servidor:")
        print(last_response)