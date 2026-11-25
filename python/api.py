from fastapi import FastAPI
from pydantic import BaseModel
import mysql.connector

app = FastAPI()

# servo1 = porta do funcionario, servo2 = porta do animal
# 180 = fechado, 90 = aberto
ABERTO = 90
FECHADO = 180

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "ZOOFEEDER"
    }


@app.get("/")
def home():
    return {"mensagem": "API funcionando"}


class RFIDPayload(BaseModel):
    uid: str
    id_recinto: int = 1  #identifica o recinto


class CommandResponse(BaseModel):
    status: str
    servo1: int
    servo2: int
    line1: str
    line2: str
    line3: str


def negado(l1, l2, l3, status="negado"):
    return CommandResponse(status=status, servo1=FECHADO, servo2=FECHADO,
                           line1=l1, line2=l2, line3=l3)


def animais_dentro(cursor, id_recinto):
    cursor.execute(
        """
        SELECT COUNT(*) AS total FROM Movimentacoes_baia m
        WHERE m.id_recinto = %s AND m.id_animais IS NOT NULL
          AND m.tipo_mov = 'Entrada'
          AND m.id_movimentacao = (
              SELECT MAX(id_movimentacao) FROM Movimentacoes_baia
              WHERE id_animais = m.id_animais
          )
        """,
        (id_recinto,)
    )
    return cursor.fetchone()["total"]


def funcionarios_dentro(cursor, id_recinto):
    """Quantos funcionarios estao dentro da baia (ultima movimentacao = Entrada)."""
    cursor.execute(
        """
        SELECT COUNT(*) AS total FROM Movimentacoes_baia m
        WHERE m.id_recinto = %s AND m.id_funcionario IS NOT NULL
          AND m.tipo_mov = 'Entrada'
          AND m.id_movimentacao = (
              SELECT MAX(id_movimentacao) FROM Movimentacoes_baia
              WHERE id_recinto = m.id_recinto AND id_funcionario = m.id_funcionario
          )
        """,
        (id_recinto,)
    )
    return cursor.fetchone()["total"]


def tratar_funcionario(cursor, conexao, funcionario, id_recinto):
    """Alterna Entrada/Saida do funcionario. Nao entra com animal na baia."""
    cursor.execute(
        """
        SELECT tipo_mov FROM Movimentacoes_baia
        WHERE id_recinto = %s AND id_funcionario = %s
        ORDER BY id_movimentacao DESC LIMIT 1
        """,
        (id_recinto, funcionario["id_funcionario"])
    )
    ultimo = cursor.fetchone()

    if ultimo and ultimo["tipo_mov"] == "Entrada":
        # Saindo: sempre permitido
        tipo = "Saida"
        resposta = CommandResponse(
            status="sucesso", servo1=FECHADO, servo2=FECHADO,
            line1="Ate logo", line2=funcionario["nome"],
            line3="Trava Fechada"
        )
    else:
        # Entrando: so se nao houver animal na baia
        if animais_dentro(cursor, id_recinto) > 0:
            return negado("Acesso Negado!", "Animal na", "baia")
        tipo = "Entrada"
        resposta = CommandResponse(
            status="sucesso", servo1=ABERTO, servo2=FECHADO,
            line1="Acesso Permitido",
            line2=f"Ola, {funcionario['nome']}",
            line3="Trava Liberada"
        )

    cursor.execute(
        "INSERT INTO Movimentacoes_baia (id_recinto, id_funcionario, tipo_mov) VALUES (%s, %s, %s)",
        (id_recinto, funcionario["id_funcionario"], tipo)
    )
    conexao.commit()
    return resposta


def tratar_animal(cursor, conexao, animal, id_recinto):
    """Alterna Entrada/Saida do animal. Entrada so com baia certa e sem funcionario dentro."""
    # 1. A tag precisa pertencer a esta baia
    if animal["id_recinto"] != id_recinto:
        return negado("Acesso Negado!", "Baia Errada", "Bloqueado")

    # 2. Ultima movimentacao desse animal
    cursor.execute(
        """
        SELECT tipo_mov FROM Movimentacoes_baia
        WHERE id_animais = %s
        ORDER BY id_movimentacao DESC LIMIT 1
        """,
        (animal["id_animais"],)
    )
    ultimo = cursor.fetchone()

    if ultimo and ultimo["tipo_mov"] == "Entrada":
        # Animal estava dentro: registra saida e FECHA
        cursor.execute(
            "INSERT INTO Movimentacoes_baia (id_recinto, id_animais, tipo_mov) VALUES (%s, %s, 'Saida')",
            (id_recinto, animal["id_animais"])
        )
        conexao.commit()
        return CommandResponse(
            status="sucesso", servo1=FECHADO, servo2=FECHADO,
            line1="Animal saiu", line2=animal["nome"], line3="Trava Fechada"
        )

    # 3. Entrada: precisa haver confirmacao de saida do funcionario
    cursor.execute(
        """
        SELECT id_funcionario, tipo_mov FROM Movimentacoes_baia
        WHERE id_recinto = %s AND id_funcionario IS NOT NULL
        ORDER BY id_movimentacao DESC LIMIT 1
        """,
        (id_recinto,)
    )
    ultima = cursor.fetchone()
    if not ultima:
        return negado("Acesso Negado!", "Sem saida", "do tratador")
    if funcionarios_dentro(cursor, id_recinto) > 0 or ultima["tipo_mov"] != "Saida":
        return negado("Acesso Negado!", "Tratador na", "baia")

    # 4. Registra entrada do animal e a alimentacao
    cursor.execute(
        "INSERT INTO Movimentacoes_baia (id_recinto, id_animais, tipo_mov) VALUES (%s, %s, 'Entrada')",
        (id_recinto, animal["id_animais"])
    )
    cursor.execute(
        "INSERT INTO Historico_alimentacao (id_animais, id_funcionario) VALUES (%s, %s)",
        (animal["id_animais"], ultima["id_funcionario"])
    )
    conexao.commit()

    return CommandResponse(
        status="sucesso", servo1=FECHADO, servo2=ABERTO,
        line1="Animal OK", line2=animal["nome"], line3="Bom apetite"
    )


@app.post("/api/validar-rfid", response_model=CommandResponse)
def validar_rfid(payload: RFIDPayload):
    conexao = None
    try:
        conexao = mysql.connector.connect(**DB_CONFIG)
        cursor = conexao.cursor(dictionary=True)

        cursor.execute(
            "SELECT id_funcionario, nome, cargo FROM Funcionario WHERE rfid = %s",
            (payload.uid,)
        )
        funcionario = cursor.fetchone()
        if funcionario:
            resposta = tratar_funcionario(cursor, conexao, funcionario, payload.id_recinto)
        else:
            cursor.execute(
                "SELECT id_animais, nome, id_recinto FROM Animais WHERE cod_tag = %s",
                (payload.uid,)
            )
            animal = cursor.fetchone()
            if animal:
                resposta = tratar_animal(cursor, conexao, animal, payload.id_recinto)
            else:
                resposta = negado("Acesso Negado!", "Tag Invalida", "Bloqueado")

        cursor.close()
        conexao.close()
        return resposta

    except Exception as err:
        print(f"[ERRO API/BD] {err}")
        if conexao and conexao.is_connected():
            conexao.close()
        return negado("Erro de Sistema", "BD Indisponivel", "Bloqueado", status="erro")

# comando para executar:
# python -m uvicorn api:app --reload