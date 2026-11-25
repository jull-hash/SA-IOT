from fastapi import FastAPI
from pydantic import BaseModel 
import mysql.connector

app = FastAPI()

@app.get("/")
def home():
    return {"mensagem": "API funcionando"}

# Configuração de conexão com o banco MySQL 
DB_CONFIG = { "host": "localhost", 
             "user": "root", 
             "password": "", 
             "database": "ZOOFEEDER"}

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
    """
    Endpoint que recebe o UID do RFID, consulta no MySQL e retorna os comandos
    dos servos e as 3 linhas do display OLED.
    """
    conexao = None
    try:
        # 1. Conecta ao MySQL
        conexao = mysql.connector.connect(**DB_CONFIG)
        cursor = conexao.cursor(dictionary=True)

        # 2. Consulta o funcionário cadastrado pelo RFID
        query_func = "SELECT id_funcionario, nome, cargo FROM Funcionario WHERE rfid = %s"
        cursor.execute(query_func, (payload.uid,))
        funcionario = cursor.fetchone()

        if funcionario:
            # 3. Registra a movimentação de entrada na baia
            query_mov = """
                INSERT INTO Movimentacoes_baia (id_recinto, id_funcionario, tipo_mov)
                VALUES (%s, %s, %s)
            """
            cursor.execute(query_mov, (1, funcionario['id_funcionario'], 'Entrada'))
            conexao.commit()

            cursor.close()
            conexao.close()

            # Retorna autorização e comandos de abertura
            return CommandResponse(
                status="sucesso",
                servo1=90,
                servo2=90,
                line1="Acesso Permitido",
                line2=f"Ola, {funcionario['nome']}",
                line3="Trava Liberada"
            )
        else:
            cursor.close()
            conexao.close()

            # Retorna recusa de acesso
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

        # Retorna erro de sistema mantendo bloqueado (RF007)
        return CommandResponse(
            status="erro",
            servo1=0,
            servo2=0,
            line1="Erro de Sistema",
            line2="BD Indisponivel",
            line3="Bloqueado"
        )




#comando para executar:
#uvicorn main:app --reload
