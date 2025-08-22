<?php
/**
 * Genera CFDI 4.0 (Tipo P) con Complemento Pagos 2.0 — SOLO XML (sin sello).
 * Guarda cfdi_pago20_pre.xml en la misma carpeta.
 *
 * PHP 7/8
 * No requiere OpenSSL ni XSLT.
 */

// ----------------- PARÁMETROS (AJUSTA A TU CASO) -----------------
$datos = [
  // Comprobante
  'Serie'              => 'P-COA',
  'Folio'              => '160',
  'LugarExpedicion'    => '61652', 
  'FormaPago'          => '99',  // <-- Forma de pago correcta para CFDI de pagos
  'MetodoPago'         => 'PPD', // <-- Método de pago correcto para CFDI de pagos
  // Emisor
  'EmisorRfc'          => 'EKU9003173C9',
  'EmisorNombre'       => 'ESCUELA KEMPER URGATE',
  'EmisorRegimen'      => '601',
  // Receptor
  'ReceptorRfc'        => 'MASO451221PM4',
  'ReceptorNombre'     => 'MARIA OLIVIA MARTINEZ SAGAZ',
  'ReceptorUsoCFDI'    => 'CP01',
  'ReceptorRegimen'    => '610',
  'ReceptorCP'         => '80290',

  // Totales Pago20 (tu ejemplo)
  'TotalTrasladosBaseIVA16'    => '33000.00',
  'TotalTrasladosImpuestoIVA16'=> '5280.00',
  'MontoTotalPagos'            => '38280.00',

  // Pago
  'FechaPago'        => '2025-07-02T00:00:00',
  'FormaDePagoP'     => '02',
  'MonedaP'          => 'MXN',
  'TipoCambioP'      => '1',
  'MontoPago'        => '38280.00',
  'NumOperacion'     => null, // si tienes, colócalo

  // DoctoRelacionado
  'UUID_DR'          => 'C3D58118-A8D0-4D88-8621-3EEB8C43D35C',
  'SerieDR'          => 'COA',
  'FolioDR'          => '196',
  'MonedaDR'         => 'MXN',
  'EquivalenciaDR'   => '1',
  'NumParcialidad'   => '1',
  'ImpSaldoAnt'      => '38280.00',
  'ImpPagado'        => '38280.00',
  'ImpSaldoInsoluto' => '0.00',

  // Impuestos DR (Traslado)
  'BaseDR'           => '33000.00',
  'ImpuestoDR'       => '002',
  'TipoFactorDR'     => 'Tasa',
  'TasaOCuotaDR'     => '0.160000',
  'ImporteDR'        => '5280.00',

  // Impuestos P (Traslado)
  'BaseP'            => '33000.00',
  'ImpuestoP'        => '002',
  'TipoFactorP'      => 'Tasa',
  'TasaOCuotaP'      => '0.160000',
  'ImporteP'         => '5280.00',
];

// ----------------- GENERACIÓN DEL XML -----------------
date_default_timezone_set('America/Mexico_City');

$xml = new DOMDocument('1.0', 'UTF-8');
$xml->formatOutput = true;

// Namespaces
$root = $xml->createElement('cfdi:Comprobante');
$root = $xml->appendChild($root);

cargaAtt($root, [
  'xmlns:cfdi' => 'http://www.sat.gob.mx/cfd/4',
  'xmlns:xsi'  => 'http://www.w3.org/2001/XMLSchema-instance',
  'xmlns:pago20' => 'http://www.sat.gob.mx/Pagos20',
  'xsi:schemaLocation' =>
    'http://www.sat.gob.mx/cfd/4 http://www.sat.gob.mx/sitio_internet/cfd/4/cfdv40.xsd ' .
    'http://www.sat.gob.mx/Pagos20 http://www.sat.gob.mx/sitio_internet/cfd/Pagos/Pagos20.xsd',
]);

cargaAtt($root, [
  'Version'            => '4.0',
  'Serie'              => $datos['Serie'],
  'Folio'              => $datos['Folio'],
  'Fecha'              => date('Y-m-d') . 'T' . date('H:i:s'),
  'Sello'              => '',       // VACÍO - lo llenará el PAC al sign_stamp
  'NoCertificado'      => '',       // VACÍO
  'Certificado'        => '',       // VACÍO
  'SubTotal'           => '0',
  'Moneda'             => 'XXX',
  'Total'              => '0',
  'TipoDeComprobante'  => 'P',
  'Exportacion'        => '01',
  'LugarExpedicion'    => $datos['LugarExpedicion'],
  //'FormaPago'          => '99',  // <-- Forma de pago correcta para CFDI de pagos
  //'MetodoPago'         => 'PPD', // <-- Método de pago correcto para CFDI de pagos
]);

// Emisor
$emisor = $xml->createElement('cfdi:Emisor');
$root->appendChild($emisor);
cargaAtt($emisor, [
  'Rfc'           => $datos['EmisorRfc'],
  'Nombre'        => $datos['EmisorNombre'],
  'RegimenFiscal' => $datos['EmisorRegimen'],
]);

// Receptor
$receptor = $xml->createElement('cfdi:Receptor');
$root->appendChild($receptor);
cargaAtt($receptor, [
  'Rfc'                      => $datos['ReceptorRfc'],
  'Nombre'                   => $datos['ReceptorNombre'],
  'UsoCFDI'                  => $datos['ReceptorUsoCFDI'],
  'RegimenFiscalReceptor'    => $datos['ReceptorRegimen'],
  'DomicilioFiscalReceptor'  => $datos['ReceptorCP'],
]);

// Conceptos: uno de "Pago"
$conceptos = $xml->createElement('cfdi:Conceptos');
$root->appendChild($conceptos);
$con = $xml->createElement('cfdi:Concepto');
$conceptos->appendChild($con);
cargaAtt($con, [
  'ClaveProdServ' => '84111506',
  'Cantidad'      => '1',
  'ClaveUnidad'   => 'ACT',
  'Descripcion'   => 'Pago',
  'ValorUnitario' => '0',
  'Importe'       => '0',
  'ObjetoImp'     => '01', // No objeto
]);

// Complemento Pagos 2.0
$compl = $xml->createElement('cfdi:Complemento');
$root->appendChild($compl);

$pagos = $xml->createElement('pago20:Pagos');
$compl->appendChild($pagos);
cargaAtt($pagos, ['Version' => '2.0']);

// Totales
$totales = $xml->createElement('pago20:Totales');
$pagos->appendChild($totales);
cargaAtt($totales, [
  // Solo se escriben si tienen valor (la función ignora null/false/'')
  'TotalTrasladosBaseIVA16'     => $datos['TotalTrasladosBaseIVA16'],
  'TotalTrasladosImpuestoIVA16' => $datos['TotalTrasladosImpuestoIVA16'],
  'MontoTotalPagos'             => $datos['MontoTotalPagos'],
]);

// Pago
$pago = $xml->createElement('pago20:Pago');
$pagos->appendChild($pago);
cargaAtt($pago, [
  'FechaPago'    => $datos['FechaPago'],
  'FormaDePagoP' => $datos['FormaDePagoP'],
  'MonedaP'      => $datos['MonedaP'],
  'TipoCambioP'  => $datos['TipoCambioP'],
  'Monto'        => $datos['MontoPago'],
  'NumOperacion' => $datos['NumOperacion'], // opcional
]);

// DoctoRelacionado
$dr = $xml->createElement('pago20:DoctoRelacionado');
$pago->appendChild($dr);
cargaAtt($dr, [
  'IdDocumento'     => $datos['UUID_DR'],
  'Serie'           => $datos['SerieDR'],
  'Folio'           => $datos['FolioDR'],
  'MonedaDR'        => $datos['MonedaDR'],
  'EquivalenciaDR'  => $datos['EquivalenciaDR'],
  'NumParcialidad'  => $datos['NumParcialidad'],
  'ImpSaldoAnt'     => $datos['ImpSaldoAnt'],
  'ImpPagado'       => $datos['ImpPagado'],
  'ImpSaldoInsoluto'=> $datos['ImpSaldoInsoluto'],
  'ObjetoImpDR'     => '02',
]);

// ImpuestosDR -> TrasladosDR
$impDR = $xml->createElement('pago20:ImpuestosDR');
$dr->appendChild($impDR);
$trasDR = $xml->createElement('pago20:TrasladosDR');
$impDR->appendChild($trasDR);
$trasladoDR = $xml->createElement('pago20:TrasladoDR');
$trasDR->appendChild($trasladoDR);
cargaAtt($trasladoDR, [
  'BaseDR'      => $datos['BaseDR'],
  'ImpuestoDR'  => $datos['ImpuestoDR'],
  'TipoFactorDR'=> $datos['TipoFactorDR'],
  'TasaOCuotaDR'=> $datos['TasaOCuotaDR'],
  'ImporteDR'   => $datos['ImporteDR'],
]);

// ImpuestosP -> TrasladosP
$impP = $xml->createElement('pago20:ImpuestosP');
$pago->appendChild($impP);
$trasP = $xml->createElement('pago20:TrasladosP');
$impP->appendChild($trasP);
$trasladoP = $xml->createElement('pago20:TrasladoP');
$trasP->appendChild($trasladoP);
cargaAtt($trasladoP, [
  'BaseP'       => $datos['BaseP'],
  'ImpuestoP'   => $datos['ImpuestoP'],
  'TipoFactorP' => $datos['TipoFactorP'],
  'TasaOCuotaP' => $datos['TasaOCuotaP'],
  'ImporteP'    => $datos['ImporteP'],
]);

// ----------------- GUARDAR -----------------
$nombreArchivo = __DIR__ . DIRECTORY_SEPARATOR . 'cfdi_pago20_pre.xml';
$xml->save($nombreArchivo);

echo "XML generado (sin sello): $nombreArchivo\n";

// ----------------- Helpers -----------------
function cargaAtt(DOMElement $nodo, array $attr) {
  foreach ($attr as $key => $val) {
    if ($val === null || $val === false) {
      continue; // no escribir atributos vacíos/false
    }
    $val = strval($val);
    $val = preg_replace('/\s\s+/', ' ', $val);
    $val = trim($val);
    if ($val === '') {
      continue;
    }
    // Regla: sin pipes y en UTF-8
    $val = str_replace('|', '/', $val);
    // DOMDocument ya maneja UTF-8 por configuración al inicio
    $nodo->setAttribute($key, $val);
  }
}
    