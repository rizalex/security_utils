<?php
if(!empty($_POST['latitude']) && !empty($_POST['longitude'])){
    //Send request and receive json data by latitude and longitude
    $url = 'https://maps.googleapis.com/maps/api/geocode/json?latlng='.trim($_POST['latitude']).','.trim($_POST['longitude']).'&sensor=false';
    $json = @file_get_contents($url);
    $data = json_decode($json);
    $status = $data->status;
    if($status=="OK"){
        //Get address from json data
        $location = $data->results[0]->formatted_address;
    }else{
        $location =  '';
    }
    //Print address 
    echo $location;
}

/**
 * This example shows settings to use when sending via Google's Gmail servers.
 */

//SMTP needs accurate times, and the PHP time zone MUST be set
//This should be done in your php.ini, but this is how to do it if you don't have access to that
date_default_timezone_set('Etc/UTC');

require 'PHPMailerAutoload.php';

//Create a new PHPMailer instance
$mail = new PHPMailer;

//Tell PHPMailer to use SMTP
$mail->isSMTP();

//Enable SMTP debugging
// 0 = off (for production use)
// 1 = client messages
// 2 = client and server messages
$mail->SMTPDebug = 2;

//Ask for HTML-friendly debug output
$mail->Debugoutput = 'html';

//Set the hostname of the mail server
$mail->Host = 'smtp.gmail.com';
// use
// $mail->Host = gethostbyname('smtp.gmail.com');
// if your network does not support SMTP over IPv6

//Set the SMTP port number - 587 for authenticated TLS, a.k.a. RFC4409 SMTP submission
$mail->Port = 587;

//Set the encryption system to use - ssl (deprecated) or tls
$mail->SMTPSecure = 'tls';

//Whether to use SMTP authentication
$mail->SMTPAuth = true;

//Username to use for SMTP authentication - use full email address for gmail
$mail->Username = "jorgermaxwell@gmail.com";

//Password to use for SMTP authentication
$mail->Password = "";

//Set who the message is to be sent from
$mail->setFrom('jorgermaxwell@gmail.com', 'First Last');

//Set an alternative reply-to address
$mail->addReplyTo('jorgermaxwell@gmail.com', 'First Last');

//Set who the message is to be sent to
$mail->addAddress('quanheng@horangi.com', 'John Doe');

//Set the subject line
$mail->Subject = 'YOLOYOGURT IN DEMAND!';

//Read an HTML message body from an external file, convert referenced images to embedded,
//convert HTML into a basic plain-text alternative body
//$mail->msgHTML(file_get_contents('contents.html'), dirname(__FILE__)).trim($_POST['latitude']).','.trim($_POST['longitude']);
$mail->msgHTML("HTML GEOLOCATE: ".trim($_POST['latitude']).','.trim($_POST['longitude'])
);

//Replace the plain text body with one created manually
$mail->AltBody = "HTML GEOLOCATE: ".trim($_POST['latitude']).','.trim($_POST['longitude']);

//send the message, check for errors
if (!$mail->send()) {
	//echo "Mailer Error: " . $mail->ErrorInfo;
} else {
	//echo "Message sent!";
}

?>