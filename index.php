<?php

require_once "conexao.php";
session_start();

$erro = " ";

if (isset($_GET["erro"])) {
    $erro = "Apenas administradores podem acessar o painel";
}

if($_SERVER["REQUEST_METHOD"] === "POST"){
    $nome = $_POST["nome"];
    $senha = $_POST["senha"];
    $st = $pdo->prepare("SELECT id_funcionario, nome, senha, cargo FROM funcionario WHERE nome = ? ");
    $st->execute([$nome]);
    $user = $st->fetch();
    if ($user && password_verify($senha ?? ' ', $user["senha"])){
        $_SESSION['usuario_id'] = $user['id_funcionario'];
        $_SESSION['usuario_nome'] = $user['nome'];
        $_SESSION['usuario_cargo'] = $user['cargo'];
        header('Location: dashboard.php');
    }else{
        $erro = "login ou senha incorretos";
    }
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
<div>
    <?php if ($erro): echo $erro; endif; ?>
</div>
<form method="POST">
    <div>
        <label>Login</label>    
        <input type="text" name="nome" placeholder="Ex.:Marcos">
    </div>    

        <div>
        <label>Senha</label>    
        <input type="password" name="senha" placeholder="••••••••">
    </div>    
        <button type="submit">enviar</button>
    </div>