<?php

session_start();

if($_SERVER["REQUEST_METHOD"] === "POST"){
    header("Location: dashboard.php");
}


?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LOGIN - JJJ</title>

</head>
<body class="bg-gray-100 min-h-screen flex">
    <form method="POST" method="">
    <div>
        <label>Login</label>    
        <input type="text" name="login" placeholder="Ex.:Marcos">
    </div>    

        <div>
        <label>Senha</label>    
        <input type="password" name="senha" placeholder="••••••••">
    </div>    
        <button type="submit">enviar</button>
    </div>