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
    $st = $pdo->prepare("SELECT * FROM animais WHERE id_animais = ?");
    $st->execute([$id]);
    $editando = $st->fetch();
}
if (isset($_GET["excluir"])) {
    $id = $_GET["excluir"];

    $cs = $pdo->prepare("DELETE FROM animais WHERE id_animais = ?");
    $cs->execute([$id]);
    header("Location: funcionario.php");
    exit;
}

if ($_SERVER["REQUEST_METHOD"] === "POST") {

    $nome = $_POST["nome"];    // ?? evita aviso se o campo não veio
    $especie = $_POST["especie"];
    $rfid = str_replace(":","",$_POST["rfid"]);
    $recinto  = $_POST["recinto"];

    if ($nome === "" || $senha === "" || $rfid === "" || $cargo === "") {
        $erro = "Preencha todos os campos!";
    } else {
        $senhahash = password_hash($senha, PASSWORD_DEFAULT);
        $st = $pdo->prepare("SELECT id_animais FROM animais WHERE nome = ?");
        $st->execute([$nome]);
        if ($st->fetch()) {
            $erro = "Animal já cadastrado";
        }
    }

    if ($erro === "") {
        $st = $pdo->prepare("INSERT INTO animais (nome,especie,cod_tag,id_recinto) VALUES (?, ?, ?, ?)");
        $st->execute([$nome,$especie,$rfid,$recinto]);

        header("Location: animal.php");     // redireciona após gravar
        exit;
    }
}

if (!$_SESSION['usuario_cargo'] === 'ADMIN'){
    header("Location: index.php");
}

$sql = "SELECT a.id_animais, a.nome, a.especie, a.cod_tag, COALESCE(r.nome_identificacao, 'Sem recinto') 
AS recinto FROM Animais a LEFT JOIN Recinto r ON a.id_recinto = r.id_recinto"; 
$anim = $pdo->query($sql);
?>
    <main class="flex-1 flex flex-col">
        <div class="bg-white border-b border-gray-200 px-6 py-4">
            <div class="flex items-center gap-2 text-xs text-gray-400 mb-1">
                <a href="dashboard.php" class="hover:text-senai-blue">dashboard</a> ›
                <span class="text-gray-700 font-semibold">Novo Animal</span>
            </div>
            <h1 class="text-xl font-extrabold text-gray-800">Novo Animal</h1>
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
                        <label class="form-label">Espécie *</label>
                        <input type="text" name="especie" class="form-input" required maxlength="100" placeholder="Felis Catus (Gato)" value= "<?= $editando["especie"] ?? "" ?>" >
                    </div>
                    <div class="mb-4">
                        <label class="form-label">RFID (Aproxime o cartão) *</label>
                        <input type="text" name="rfid" class="form-input" required min="0" step="0.01" placeholder="Ex: 123:456:678" value= "<?= $editando["cod_tag"] ?? "" ?>">
                    </div>
                    <div class="mb-6">
                        <label class="form-label">Recinto *</label>
                        <select id="recinto" name="recinto" required>
                            <option value="" selected>--Escolha um recinto--</option>
                            <option value="1">Baia 01 - Savana Grandes Felinos</option>
                            <option value="2" >Baia 02 - Aviário Tropical</option>
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
            <h3 class="text-lg font-bold text-gray-800 mb-4">Animais</h3>
            <table class="w-full text-sm">
                <thead>
                    <tr class="bg-gray-800 text-white">
                        <th class="px-4 py-3 text-left rounded-tl-lg">ID</th>
                        <th class="px-4 py-3 text-left">Nome</th>
                        <th class="px-4 py-3 text-left">especie</th>
                        <th class="px-4 py-3 text-left">Recinto</th>
                        <th class="px-4 py-3 text-left">Ações</th>
                    </tr>
                </thead>
                <tbody>
                    <?php while ($u = $anim->fetch(PDO::FETCH_ASSOC)): ?>
                        <tr class="border-b border-gray-200 hover:bg-gray-50">
                            <td class="px-4 py-3"><?php echo $u["id_animais"]; ?></td>
                            <td class="px-4 py-3"style="max-width: 200px; overflow-wrap: break-word; word-break: break-word;"><?php  echo $u["nome"]; ?></td>
                            <td class="px-4 py-3"><?php echo $u["especie"]; ?></td>
                            <td class="px-4 py-3"><?php echo $u["recinto"]; ?></td>
                            <td class="px-4 py-3 text-center">
                                <div class="flex items-center justify-center gap-1.5">
                                    
                                    <a href="animal.php?editar=<?= $u["id_animais"] ?>" 
                                    class="bg-yellow-500 text-white text-xs px-2.5 py-1.5 rounded-md hover:bg-yellow-700 transition" 
                                    title="Editar">✏ Editar
                                </a>

                                    <a href="animal.php?excluir=<?= $u["id_animais"] ?>"
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