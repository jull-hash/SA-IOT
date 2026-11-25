<<<<<<< Updated upstream:SA/php/conexao.php
<?php
// ============================================
// Arquivo: conexao.php
// Função: Conectar o PHP ao banco de dados MySQL
// ============================================

// Dados de conexão com o banco
$servidor = "localhost";
$usuario  = "root";
$senha    = "";
$banco    = "zoo";

// Criar a conexão usando mysqli
$conexao = mysqli_connect($servidor, $usuario, $senha, $banco);

// Verificar se a conexão funcionou
if (!$conexao) {
    die("Erro ao conectar com o banco de dados: " . mysqli_connect_error());
}

// Definir o charset para aceitar acentos
mysqli_set_charset($conexao, "utf8mb4");
=======
<?php
// ============================================
// Arquivo: conexao.php
// Função: Conectar o PHP ao banco de dados MySQL usando PDO
// ============================================

// Dados de conexão com o banco
$host  = 'localhost';
$banco = 'ZOOFEEDER';
$user  = 'root';
$senha = '';                     // no WampServer o root vem sem senha

try {
    $pdo = new PDO(
        "mysql:host=$host;dbname=$banco;charset=utf8mb4",
        $user,
        $senha,
        [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]
    );
} catch (PDOException $e) {
    exit('Falha na conexão: ' . $e->getMessage());
}
>>>>>>> Stashed changes:php/conexao.php
