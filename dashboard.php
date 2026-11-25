<?php
session_start();
require_once "conexao.php";

// Quando o login gravar a sessao:
if (!isset($_SESSION['usuario_id'])) { 
    header("Location: index.php");
}
if ($_SESSION['usuario_cargo'] !== 'Admin'){
    header("Location: index.php");
}

// Quem esta dentro agora 
$dentro = $pdo->query("
    SELECT r.nome_identificacao AS baia,
           COALESCE(f.nome, a.nome) AS nome,
           IF(m.id_funcionario IS NULL, 'Animal', 'Funcionário') AS tipo,
           m.data_hora
    FROM Movimentacoes_baia m
    JOIN Recinto r ON r.id_recinto = m.id_recinto
    LEFT JOIN Funcionario f ON f.id_funcionario = m.id_funcionario
    LEFT JOIN Animais a ON a.id_animais = m.id_animais
    WHERE m.tipo_mov = 'Entrada'
      AND m.id_movimentacao = (
          SELECT MAX(m2.id_movimentacao) FROM Movimentacoes_baia m2
          WHERE (m.id_funcionario IS NOT NULL AND m2.id_funcionario = m.id_funcionario)
             OR (m.id_animais IS NOT NULL AND m2.id_animais = m.id_animais)
      )
    ORDER BY m.data_hora DESC
")->fetchAll();

$qtdFunc   = count(array_filter($dentro, fn($d) => $d['tipo'] === 'Funcionário'));
$qtdAnimal = count($dentro) - $qtdFunc;

// Ultimas movimentacoes
$movs = $pdo->query("
    SELECT m.data_hora, r.nome_identificacao AS baia,
           COALESCE(f.nome, a.nome) AS nome,
           IF(m.id_funcionario IS NULL, 'Animal', 'Funcionário') AS tipo,
           m.tipo_mov
    FROM Movimentacoes_baia m
    JOIN Recinto r ON r.id_recinto = m.id_recinto
    LEFT JOIN Funcionario f ON f.id_funcionario = m.id_funcionario
    LEFT JOIN Animais a ON a.id_animais = m.id_animais
    ORDER BY m.id_movimentacao DESC
    LIMIT 10
")->fetchAll();

// Historico de alimentacao
$alim = $pdo->query("
    SELECT h.data_hora, a.nome AS animal, a.cod_tag, f.nome AS tratador
    FROM Historico_alimentacao h
    JOIN Animais a ON a.id_animais = h.id_animais
    JOIN Funcionario f ON f.id_funcionario = h.id_funcionario
    ORDER BY h.id_alimentacao DESC
    LIMIT 10
")->fetchAll();

$hoje = $pdo->query("SELECT COUNT(*) FROM Historico_alimentacao WHERE DATE(data_hora) = CURDATE()")->fetchColumn();

function h($v) { return htmlspecialchars((string)$v, ENT_QUOTES, 'UTF-8'); }
function dt($v) { return date('d/m/Y H:i:s', strtotime($v)); }
?>
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="10">
    <title>Painel administrativo</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <header class="bg-gray-900 text-white px-6 py-4 flex items-center justify-between">
        <h1 class="font-bold text-lg">Painel administrativo</h1>
        <nav class="flex gap-4 text-sm">
            <a href="animal.php" class="font-semibold">Cadastrar animal</a>
            <a href="funcionario.php" class="font-semibold">Cadastrar funcionários</a>
            <a href="dashboard.php" class="font-semibold">Dashboard</a>
            <a href="sair.php" class="text-gray-300 hover:text-white">Sair</a>
        </nav>
    </header>

    <main class="max-w-5xl mx-auto p-6 space-y-6">

        <!-- Cards -->
        <section class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="bg-white rounded-lg shadow p-5">
                <p class="text-xs uppercase text-gray-500 font-semibold">Funcionários na baia</p>
                <p class="text-3xl font-bold text-gray-800 mt-1"><?= $qtdFunc ?></p>
            </div>
            <div class="bg-white rounded-lg shadow p-5">
                <p class="text-xs uppercase text-gray-500 font-semibold">Animais na baia</p>
                <p class="text-3xl font-bold text-gray-800 mt-1"><?= $qtdAnimal ?></p>
            </div>
            <div class="bg-white rounded-lg shadow p-5">
                <p class="text-xs uppercase text-gray-500 font-semibold">Alimentações hoje</p>
                <p class="text-3xl font-bold text-gray-800 mt-1"><?= (int)$hoje ?></p>
            </div>
        </section>

        <!-- Quem esta dentro -->
        <section class="bg-white rounded-lg shadow p-5">
            <h2 class="font-semibold text-gray-800 mb-3">Dentro da baia agora</h2>
            <table class="w-full text-sm">
                <thead>
                    <tr class="text-left text-gray-500 border-b">
                        <th class="py-2">Baia</th><th>Nome</th><th>Tipo</th><th>Desde</th>
                    </tr>
                </thead>
                <tbody>
                <?php if (!$dentro): ?>
                    <tr><td colspan="4" class="py-3 text-gray-400">Ninguém na baia.</td></tr>
                <?php endif; ?>
                <?php foreach ($dentro as $d): ?>
                    <tr class="border-b last:border-0">
                        <td class="py-2"><?= h($d['baia']) ?></td>
                        <td><?= h($d['nome']) ?></td>
                        <td><?= h($d['tipo']) ?></td>
                        <td><?= h(dt($d['data_hora'])) ?></td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </section>

        <!-- Últimas movimentações -->
        <section class="bg-white rounded-lg shadow p-5">
            <h2 class="font-semibold text-gray-800 mb-3">Últimas movimentações</h2>
            <table class="w-full text-sm">
                <thead>
                    <tr class="text-left text-gray-500 border-b">
                        <th class="py-2">Data/hora</th><th>Baia</th><th>Nome</th><th>Tipo</th><th>Movimento</th>
                    </tr>
                </thead>
                <tbody>
                <?php if (!$movs): ?>
                    <tr><td colspan="5" class="py-3 text-gray-400">Nenhuma movimentação.</td></tr>
                <?php endif; ?>
                <?php foreach ($movs as $m): ?>
                    <tr class="border-b last:border-0">
                        <td class="py-2"><?= h(dt($m['data_hora'])) ?></td>
                        <td><?= h($m['baia']) ?></td>
                        <td><?= h($m['nome']) ?></td>
                        <td><?= h($m['tipo']) ?></td>
                        <td>
                            <span class="px-2 py-0.5 rounded text-xs font-semibold <?= $m['tipo_mov'] === 'Entrada' ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-700' ?>">
                                <?= $m['tipo_mov'] === 'Entrada' ? 'Entrada' : 'Saída' ?>
                            </span>
                        </td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </section>

        <!-- Historico de alimentacao -->
        <section class="bg-white rounded-lg shadow p-5">
            <h2 class="font-semibold text-gray-800 mb-3">Histórico de alimentação</h2>
            <table class="w-full text-sm">
                <thead>
                    <tr class="text-left text-gray-500 border-b">
                        <th class="py-2">Data/hora</th><th>Animal</th><th>Tag</th><th>Tratador</th>
                    </tr>
                </thead>
                <tbody>
                <?php if (!$alim): ?>
                    <tr><td colspan="4" class="py-3 text-gray-400">Nenhuma alimentação registrada.</td></tr>
                <?php endif; ?>
                <?php foreach ($alim as $a): ?>
                    <tr class="border-b last:border-0">
                        <td class="py-2"><?= h(dt($a['data_hora'])) ?></td>
                        <td><?= h($a['animal']) ?></td>
                        <td><?= h($a['cod_tag']) ?></td>
                        <td><?= h($a['tratador']) ?></td>
                    </tr>
                <?php endforeach; ?>
                </tbody>
            </table>
        </section>

        <p class="text-xs text-gray-400 text-center">Atualiza sozinho a cada 10 segundos.</p>
    </main>
</body>
</html>