<?php
$username = 'ricascor080@gmail.com';
$password = 'Ricas002385.'; // La contraseña proporcionada por la plataforma Finkok.Tipo String
$taxpayer_id = 'EKU9003173C9'; // RFC del emisor
$rfcreceptor = '';
$invoices = 'A2A4E302-A29E-5A84-8962-226AD3E700AC';
$cer_path = '/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/cer.pem';
$cer_file = fopen($cer_path, "r");
$cer_content =fread($cer_file, filesize($cer_path));
fclose($cer_file);
//$cer_content = base64_encode($cer_content);
$key_path = '/home/rcornejo/Descargas/CFDI PRACTICA php/CFDI PRACTICA/key.pem';
$key_file = fopen($key_path, "r");
$key_content =fread($key_file, filesize($key_path));
fclose($key_file);
//$key_content = base64_encode($key_content);

$url = "https://demo-facturacion.finkok.com/servicios/soap/cancel.wsdl";
$client = new SoapClient($url);
$params = array(
                'username' => $username,
                'password' => $password,
                'taxpayer_id' => $taxpayer_id,
                'rtaxpayer_id' => $rfcreceptor,
                'uuid' => $invoices,
                'cer' => $cer_content,
                'key' => $key_content);
print_r($params);

$response = $client->__soapCall("get_related", array($params));
echo "REQUEST:\n" . $client->__getLastRequest() . "\n";
print_r($response);

 ?>