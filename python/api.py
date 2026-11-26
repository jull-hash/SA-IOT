from fastapi import FastAPI
from pydantic import BaseModel
import mysql.connector


app = FastAPI()


# servo1 = porta do funcionario, servo2 = porta do animal
# 0 = fechado, 90 = aberto
ABERTO = 90
FECHADO = 0


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "zoo"
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


#só considera mov de animais, igual o de funcionários (Is not null)
#busca só as movs mais recentes do funcionário (Select max)
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


#verifica se o funcionario esta dentro da baia, ou seja, se a ultima movimentacao foi Entrada
def funcionarios_dentro(cursor, id_recinto):
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


#le no banco o estado real das portas da baia: porta do funcionario aberta se ha funcionario dentro,
#porta do animal aberta se ha animal dentro
def estado_portas(cursor, id_recinto):
    servo1 = ABERTO if funcionarios_dentro(cursor, id_recinto) > 0 else FECHADO
    servo2 = ABERTO if animais_dentro(cursor, id_recinto) > 0 else FECHADO
    return servo1, servo2


#acesso negado que NAO mexe nas portas: manda de volta o estado atual de cada uma
def negado_mantendo(cursor, id_recinto, l1, l2, l3):
    servo1, servo2 = estado_portas(cursor, id_recinto)
    return CommandResponse(status="negado", servo1=servo1, servo2=servo2,
                           line1=l1, line2=l2, line3=l3)




#troca entre entrada e saida do funcionario, se ele estiver entrando, verifica se nao ha animal dentro da baia
def tratar_funcionario(cursor, conexao, funcionario, id_recinto):
    cursor.execute(
        """
        SELECT tipo_mov FROM Movimentacoes_baia
        WHERE id_recinto = %s AND id_funcionario = %s
        ORDER BY id_movimentacao DESC LIMIT 1
        """,
        (id_recinto, funcionario["id_funcionario"])
    )
    ultimo = cursor.fetchone()


#só entra se não houver animal dentro da baia
    if ultimo and ultimo["tipo_mov"] == "Entrada":
        tipo = "Saida"
        resposta = CommandResponse(
            status="sucesso", servo1=FECHADO, servo2=FECHADO,
            line1="Ate logo", line2=funcionario["nome"],
            line3="Trava Fechada"
        )
    else:
        # funcionario precisa ter saido de qualquer outra baia antes de entrar
        cursor.execute(
            """
            SELECT id_recinto, tipo_mov FROM Movimentacoes_baia
            WHERE id_funcionario = %s
            ORDER BY id_movimentacao DESC LIMIT 1
            """,
            (funcionario["id_funcionario"],)
        )
        atual = cursor.fetchone()
        if atual and atual["tipo_mov"] == "Entrada" and atual["id_recinto"] != id_recinto:
            return negado_mantendo(cursor, id_recinto, "Acesso Negado!", "Saia da baia", str(atual["id_recinto"]))


        if animais_dentro(cursor, id_recinto) > 0:
            return negado_mantendo(cursor, id_recinto, "Acesso Negado!", "Animal na", "baia")
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


#o animal só entra se o funcionário não estiver no recinto e verifica se o recinto é correspodente ao animal
def tratar_animal(cursor, conexao, animal, id_recinto):
    
    if animal["id_recinto"] != id_recinto:
        return negado_mantendo(cursor, id_recinto, "Acesso Negado!", "Baia Errada", "Bloqueado")


    cursor.execute(
        """
        SELECT tipo_mov FROM Movimentacoes_baia
        WHERE id_animais = %s
        ORDER BY id_movimentacao DESC LIMIT 1
        """,
        (animal["id_animais"],)
    )
    ultimo = cursor.fetchone()


# Registra a saida do animal se a ultima movimentacao foi entrada
    if ultimo and ultimo["tipo_mov"] == "Entrada":
        cursor.execute(
            "INSERT INTO Movimentacoes_baia (id_recinto, id_animais, tipo_mov) VALUES (%s, %s, 'Saida')",
            (id_recinto, animal["id_animais"])
        )
        conexao.commit()
        return CommandResponse(
            status="sucesso", servo1=FECHADO, servo2=FECHADO,
            line1="Animal saiu", line2=animal["nome"], line3="Trava Fechada"
        )


# se o funcionário estiver dentro do recinto, o animal não pode entrar
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
        return negado_mantendo(cursor, id_recinto, "Acesso Negado!", "Sem saida", "do tratador")
    if funcionarios_dentro(cursor, id_recinto) > 0 or ultima["tipo_mov"] != "Saida":
        return negado_mantendo(cursor, id_recinto, "Acesso Negado!", "Tratador na", "baia")


#registrando entrada e histpórico de alimentação do animal
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
                # guarda a tag desconhecida para o admin poder cadastra-la
                try:
                    cursor.execute(
                        "INSERT INTO Tag_lida (uid) VALUES (%s) "
                        "ON DUPLICATE KEY UPDATE ultima_leitura = NOW()",
                        (payload.uid,)
                    )
                    conexao.commit()
                except Exception as e:
                    print(f"[AVISO] Nao foi possivel salvar a tag lida: {e}")
                resposta = negado_mantendo(cursor, payload.id_recinto, "Acesso Negado!", "Tag Invalida", "Bloqueado")


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