<?php

$username = 'ricascor080@gmail.com'; # Usuario de Finkok
$password = 'Ricas002385.'; # Contraseña de Finkok

# Leer el archivo xml y codificarlo en la base 64
$invoice_path = "C:\\Users\\ricas\\Downloads\\CFDI PRACTICA\\php\\cfdi_pago20_pre.xml";
$xml_file = fopen($invoice_path, "rb");
$xml_content = fread($xml_file, filesize($invoice_path));   
fclose($xml_file);

# Se almacenan las variables con los datos en el array $params
$params = array(
"xml" => $xml_content,
"username" => $username,
"password" => $password
);

# Petición al web service
$client = new SoapClient("https://demo-facturacion.finkok.com/servicios/soap/stamp.wsdl", array('trace' => 1));
$result = $client->__soapCall("sign_stamp", array($params));
# Imprimir la respuesta del web service en pantalla
#echo "REQUEST:\n" . $client->__getLastRequest() . "\n";
$request = $client->__getLastRequest();
$response = $client->__getLastResponse();

print_r($request);
print_r($response);

// Guardar archivos SoapRequest.xml y SoapResponse.xml en la misma carpeta del script
$requestPath  = "C:\\Users\\ricas\\Downloads\\CFDI PRACTICA\\php\\SoapRequest.xml";
$responsePath = "C:\\Users\\ricas\\Downloads\\CFDI PRACTICA\\php\\SoapResponse.xml";

file_put_contents($requestPath,  $client->__getLastRequest()  . PHP_EOL);
file_put_contents($responsePath, $client->__getLastResponse() . PHP_EOL);   
?>  