#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from datetime import datetime
import sys
import logging

from zeep import Client, Settings
from zeep.plugins import HistoryPlugin
from lxml import etree

# --------- LOGGING ÚTIL ----------
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
for name in ("zeep.client", "zeep.transport", "zeep.xsd.schema", "zeep.wsdl"):
    logging.getLogger(name).setLevel(logging.WARNING)

# --------- CREDENCIALES (USA VARIABLES DE ENTORNO EN PRODUCCIÓN) ----------
USERNAME = "ricascor080@gmail.com"
PASSWORD = "Ricas002385."

# --------- WSDL DEMO ----------
STAMP_WSDL = "https://demo-facturacion.finkok.com/servicios/soap/stamp.wsdl"

def pick_xml_path():
    """Regresa la ruta al XML a timbrar:
       1) sys.argv[1] si viene
       2) 'cfdi_ejemplo.xml' junto al script
       3) el *.xml más reciente junto al script
    """
    script_dir = Path(__file__).resolve().parent

    # 1) argumento
    if len(sys.argv) > 1:
        arg = Path(sys.argv[1]).expanduser().resolve()
        if arg.is_file():
            return arg
        raise FileNotFoundError(f"No se encontró el archivo indicado: {arg}")

    # 2) cfdi_ejemplo.xml
    candidate = (script_dir / "cfdi_ejemplo.xml")
    if candidate.is_file():
        return candidate.resolve()

    # 3) más reciente *.xml (excluye salidas conocidas)
    xmls = [p for p in script_dir.glob("*.xml")
            if p.name not in {"request.xml", "response.xml"} and not p.name.startswith("stamp_")]
    if not xmls:
        raise FileNotFoundError(
            f"No se encontró 'cfdi_ejemplo.xml' ni ningún *.xml en {script_dir}.\n"
            "Pasa la ruta del XML como argumento: python3 timbrar_cfdi.py \"/ruta/al/archivo.xml\""
        )
    xmls.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    logging.warning("No se indicó ruta; usando el XML más reciente: %s", xmls[0].name)
    return xmls[0].resolve()

def save_bytes(path: Path, data: bytes):
    path.write_bytes(data)
    logging.info("Archivo guardado: %s", path)

def main():
    xml_path = pick_xml_path()
    logging.info("Cargando XML desde: %s", xml_path)

    # Lee en binario
    xml_bytes = xml_path.read_bytes()
    if not xml_bytes.strip().startswith(b"<"):
        logging.warning("El archivo no parece XML (no inicia con '<'). Se enviará tal cual.")

    # Cliente SOAP con history para capturar envolturas
    history = HistoryPlugin()
    settings = Settings(strict=False, xml_huge_tree=True)
    client = Client(wsdl=STAMP_WSDL, settings=settings, plugins=[history])

    # Llamada a stamp (xml base64Binary, Zeep lo maneja con bytes)
    logging.info("Timbrando con Finkok demo...")
    try:
        resp = client.service.sign_stamp(xml_bytes, USERNAME, PASSWORD)
    except Exception as e:
        # Guarda SOAP aunque haya error
        try:
            if history.last_sent:
                req_env = etree.tostring(history.last_sent["envelope"], pretty_print=True, encoding="utf-8")
                save_bytes(Path("request.xml"), req_env)
            if history.last_received:
                res_env = etree.tostring(history.last_received["envelope"], pretty_print=True, encoding="utf-8")
                save_bytes(Path("response.xml"), res_env)
        except Exception:
            pass
        raise

    # Extrae campos comunes
    uuid = getattr(resp, "UUID", None)
    cod_estatus = getattr(resp, "CodEstatus", None)
    fecha = getattr(resp, "Fecha", None)
    stamped_xml = getattr(resp, "xml", None)

    logging.info("Resultado Finkok: UUID=%s, CodEstatus=%s, Fecha=%s", uuid, cod_estatus, fecha)

    # Guarda XML timbrado (si viene)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_name = f"stamp_cfdi4.xml"
    if stamped_xml:
        # resp.xml puede venir como bytes o str; normaliza a bytes
        data = stamped_xml if isinstance(stamped_xml, (bytes, bytearray)) else str(stamped_xml).encode("utf-8")
        save_bytes(Path(out_name), data)
    else:
        logging.warning("No vino 'xml' en la respuesta. Revisa response.xml.")

    # Guarda SOAP Request/Response
    if history.last_sent:
        req_env = etree.tostring(history.last_sent["envelope"], pretty_print=True, encoding="utf-8")
        save_bytes(Path("request.xml"), req_env)
    if history.last_received:
        res_env = etree.tostring(history.last_received["envelope"], pretty_print=True, encoding="utf-8")
        save_bytes(Path("response.xml"), res_env)

if __name__ == "__main__":
    main()
