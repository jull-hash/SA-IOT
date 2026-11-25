from fastapi import FastAPI
from pydantic import BaseModel
import mysql.connector

app = FastAPI()

@app.get("/")
def home():
    return {"mensagem": "API funcionando"}

# Configuração de conexão com o banco MySQL
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "zoo"
}

# Modelo de dados recebido do Python/MQTT
class RFIDPayload(BaseModel):
    uid: str

# Modelo de dados retornado para o Python/MQTT
class CommandResponse(BaseModel):
    status: str
    servo1: int
    servo2: int
    line1: str
    line2: str
    line3: str

@app.post("/api/validar-rfid", response_model=CommandResponse)
def validar_rfid(payload: RFIDPayload):
    conexao = None
    try:
        # 1. Conecta ao MySQL
        conexao = mysql.connector.connect(**DB_CONFIG)
        cursor = conexao.cursor(dictionary=True)

        # 2. Consulta o funcionário cadastrado pelo RFID
        cursor.execute(
            "SELECT id_funcionario, nome, cargo FROM Funcionario WHERE rfid = %s",
            (payload.uid,)
        )
        funcionario = cursor.fetchone()

        if funcionario:
            # 3. Busca a ÚLTIMA movimentação desse funcionário no recinto 1
            cursor.execute(
                """
                SELECT tipo_mov FROM Movimentacoes_baia
                WHERE id_recinto = %s AND id_funcionario = %s
                ORDER BY id_movimentacao DESC LIMIT 1
                """,
                (1, funcionario["id_funcionario"])
            )
            ultimo = cursor.fetchone()

            # 4. Decide: se o último foi 'Entrada', agora é saída (fecha)
            if ultimo and ultimo["tipo_mov"] == "Entrada":
                tipo = "Saida"
                resposta = CommandResponse(
                    status="sucesso",
                    servo1=180,
                    servo2=180,
                    line1="Ate logo",
                    line2=funcionario["nome"],
                    line3="Trava Fechada"
                )
            else:
                tipo = "Entrada"
                resposta = CommandResponse(
                    status="sucesso",
                    servo1=90,
                    servo2=180,
                    line1="Acesso Permitido",
                    line2=f"Ola, {funcionario['nome']}",
                    line3="Trava Liberada"
                )

            # 5. Registra a movimentação no banco
            cursor.execute(
                "INSERT INTO Movimentacoes_baia (id_recinto, id_funcionario, tipo_mov) VALUES (%s, %s, %s)",
                (1, funcionario["id_funcionario"], tipo)
            )
            conexao.commit()

            cursor.close()
            conexao.close()
            return resposta

        else:
            cursor.close()
            conexao.close()
            return CommandResponse(
                status="negado",
                servo1=0,
                servo2=0,
                line1="Acesso Negado!",
                line2="Tag Invalida",
                line3="Bloqueado"
            )

    except Exception as err:
        print(f"[ERRO API/BD] {err}")
        if conexao and conexao.is_connected():
            conexao.close()
        return CommandResponse(
            status="erro",
            servo1=0,
            servo2=0,
            line1="Erro de Sistema",
            line2="BD Indisponivel",
            line3="Bloqueado"
        )

# comando para executar:
# python -m uvicorn main:app --reload