<?php
session_start();
require_once 'conexao.php';

if (!isset($_SESSION['usuario_id'])) { 
    header("Location: index.php");
}
if ($_SESSION['usuario_cargo'] !== 'Admin'){
    header("Location: index.php");
}


$erro = "";

$nome = " ";
$senha = " ";
$rfid = " ";
$cargo = " ";
$editando = " ";

if (isset($_GET["editar"])) {
    $id = $_GET["editar"];
    $st = $pdo->prepare("SELECT * FROM funcionario WHERE id_funcionario = ?");
    $st->execute([$id]);
    $editando = $st->fetch();
}
if (isset($_GET["excluir"])) {
    $id = $_GET["excluir"];

    $cs = $pdo->prepare("DELETE FROM funcionario WHERE id_funcionario = ?");
    $cs->execute([$id]);
    header("Location: funcionario.php");
    exit;
}

if ($_SERVER["REQUEST_METHOD"] === "POST") {

    $nome = $_POST["nome"];
    $user = $_POST["nome"];       // ?? evita aviso se o campo não veio
    $senha = $_POST["senha"];
    $rfid = str_replace(":","",$_POST["rfid"]);
    $cargo  = $_POST["cargo"];

    if ($nome === "" || $senha === "" || $rfid === "" || $cargo === "") {
        $erro = "Preencha todos os campos!";
    } else {
        $senhahash = password_hash($senha, PASSWORD_DEFAULT);
        $st = $pdo->prepare("SELECT id_funcionario FROM funcionario WHERE nome = ?");
        $st->execute([$nome]);
        if ($st->fetch()) {
            $erro = "Usuário já cadastrado!";
        }
    }

    if ($erro === "") {
        $st = $pdo->prepare("INSERT INTO funcionario (rfid, nome,  cargo, usuario, senha) VALUES (?, ?, ?,?, ?)");
        $st->execute([$rfid, $nome, $cargo, $user, $senhahash]);

        header("Location: funcionario.php");     // redireciona após gravar
        exit;
    }
}

$sql = "SELECT id_funcionario, nome, cargo, rfid from funcionario"; 
$fun = $pdo->query($sql);

if (!$_SESSION['usuario_cargo'] === 'ADMIN'){
    header("Location: index.php");
}
?>
    <main class="flex-1 flex flex-col">
        <div class="bg-white border-b border-gray-200 px-6 py-4">
            <div class="flex items-center gap-2 text-xs text-gray-400 mb-1">
                <a href="dashboard.php" class="hover:text-senai-blue">dashboard</a> ›
                <span class="text-gray-700 font-semibold">Novo Funcionário</span>
            </div>
            <h1 class="text-xl font-extrabold text-gray-800"><?= $editando ? "Preencha o formulário abaixo para atualizar os dados." : "Preencha os dados abaixo para cadastrar um novo funcionario." ?></h1>
        </div>
        <div class="p-6 flex-1 max-w-xl">

            <?php if (!empty($erro)): ?>
                <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
                    <?= $erro ?>
                </div>
            <?php endif; ?>

            <div class="bg-white rounded-xl shadow-sm p-6">
                <form method="post">
                    <div class="mb-4">
                        <label class="form-label">Nome *</label>
                        <input type="text" name="nome" class="form-input" required maxlength="100" placeholder="Ex: Carlos" value= "<?= $editando["nome"] ?? "" ?>" >
                    </div>
                    <div class="mb-4">
                        <label class="form-label">Senha *</label>
                        <input type="text" name="senha" class="form-input" required maxlength="100" placeholder="••••••••••" >
                    </div>
                    <div class="mb-4">
                        <label class="form-label">RFID (Aproxime o cartão) *</label>
                        <input type="text" name="rfid" class="form-input" required min="0" step="0.01" placeholder="Ex: 123:456:678" value= "<?= $editando["rfid"] ?? "" ?>" >
                    </div>
                    <div class="mb-6">
                        <label class="form-label">Cargo *</label>
                        <select id="cargo" name="cargo" required>
                            <option value="" selected>--Escolha um cargo--</option>
                            <option value="Tratador Sênior">Tratador Sênior</option>
                            <option value="Veterinário" >Veterinário</option>
                            <option value="Tratador Pleno">Tratador Pleno</option>
                            <option value="Biólogo" >Biólogo</option>
                            <option value="Tratador">Tratador</option>
                            <option value="Admin">ADMIN</option>
                        </select>
                    </div>

                    <div class="flex gap-2">
                        <button type="submit" class="bg-senai-blue text-white font-bold px-5 py-2.5 rounded-lg text-sm hover:bg-senai-blue-dark transition">💾 Salvar</button>
                        <a href="dashboard.php" class="bg-gray-100 text-gray-600 font-semibold px-5 py-2.5 rounded-lg text-sm hover:bg-gray-200 transition">Cancelar</a>
                    </div>
                </form>
            </div>
        </div>

        <div class="container-tabela">
            <h3 class="text-lg font-bold text-gray-800 mb-4">Funcionários</h3>
            <table class="w-full text-sm">
                <thead>
                    <tr class="bg-gray-800 text-white">
                        <th class="px-4 py-3 text-left rounded-tl-lg">ID</th>
                        <th class="px-4 py-3 text-left">Nome</th>
                        <th class="px-4 py-3 text-left">cargo</th>
                        <th class="px-4 py-3 text-left">RFID</th>
                        <th class="px-4 py-3 text-left">Ações</th>
                    </tr>
                </thead>
                <tbody>
                    <?php while ($u = $fun->fetch(PDO::FETCH_ASSOC)): ?>
                        <tr class="border-b border-gray-200 hover:bg-gray-50">
                            <td class="px-4 py-3"><?php echo $u["id_funcionario"]; ?></td>
                            <td class="px-4 py-3"style="max-width: 200px; overflow-wrap: break-word; word-break: break-word;"><?php  echo $u["nome"]; ?></td>
                            <td class="px-4 py-3"><?php echo $u["cargo"]; ?></td>
                            <td class="px-4 py-3"><?php echo $u["rfid"]; ?></td>
                            <td class="px-4 py-3 text-center">
                                <div class="flex items-center justify-center gap-1.5">
                                    
                                    <a href="funcionario.php?editar=<?= $u["id_funcionario"] ?>" 
                                    class="bg-yellow-500 text-white text-xs px-2.5 py-1.5 rounded-md hover:bg-yellow-700 transition" 
                                    title="Editar">✏ Editar
                                </a>

                                    <a href="funcionario.php?excluir=<?= $u["id_funcionario"] ?>"
                                    <button onclick="return confirm('Excluir este produto?')" 
                                    class="bg-red-500 text-white text-xs px-2.5 py-1.5 rounded-md hover:bg-red-700 transition" 
                                    title="Excluir">🗑</button>
                                </a>

                                </div>
                            </td>

 
                            
                        </tr>
                    <?php endwhile; ?>
                </tbody>
            </table>
        </div>

    </main>
</body>
</html>