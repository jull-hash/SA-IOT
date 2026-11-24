import json
import time
import threading
import paho.mqtt.client as mqtt


FUNCIONARIOS_AUTORIZADOS = { "01020304": {"nome": "Jailine", "cargo": "Tratador"},
"A1B2C3D4": {"nome": "Julio", "cargo": "Tratador"},
"12345678": {"nome": "Juliana", "cargo": "Veterinária"} }


MQTT_SERVER = "broker.mqtt.cool"
MQTT_PORT = 1883


MQTT_ROOT = "mango/esp32c3/SA"

TOPIC_RFID = f"{MQTT_ROOT}/rfid"
TOPIC_COMMAND = f"{MQTT_ROOT}/command"
TOPIC_ALL = f"{MQTT_ROOT}/#"

CLIENT_ID = "Python-Client-juliana"

connected = threading.Event()

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[MQTT] Conectado ao broker!")
        client.subscribe(TOPIC_ALL)
        print(f"[MQTT] Inscrito em: {TOPIC_ALL}")
        connected.set()
    else:
        print(f"[MQTT] Falha na conexao: {reason_code}")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    connected.clear()
    print(f"[MQTT] Desconectado: {reason_code}")


def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"\n[MQTT] {topic}: {msg.payload!r}")
        return
    print("\n" + "=" * 50)
   
    # if topic == TOPIC_RFID
    #     print("[ESP32] TELEMETRIA")
    #     print(f"Jogador 1: {payload.get('jogador1')}")
    #     print(f"Jogador 2: {payload.get('jogador2')}")
    #     j1 = payload.get("jogador1")
    #     j2 = payload.get("jogador2")
    #     vencedor = calcular_vencedor(j1, j2)
    #     print(f"Vencedor: {vencedor}")
    #     line1 = "Vencedor: "
    #     line2 = vencedor
    #     line3 = ""
    #     send_command(line1, line2, line3)
   
    if topic == TOPIC_RFID:
        rfid = payload.get("uid")
        print("[ESP32] RFID")
        print(f"UID: {rfid}")
        servo1, servo2, line1, line2, line3 = abrir_trava(rfid)
        send_command(servo1, servo2, line1, line2, line3)
       
    elif topic == TOPIC_COMMAND:
        print("[MQTT] COMANDO PUBLICADO")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"[MQTT] Topico: {topic}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("=" * 50)


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=CLIENT_ID
)



def abrir_trava(rfid):
    funcionario = FUNCIONARIOS_AUTORIZADOS.get(rfid)
    if funcionario:
        return 90, 180, "Liberado", funcionario["nome"], funcionario["cargo"]
    return 90, 90, "Negado", "Tag", "invalida"
       
   
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message


def send_command(servo1, servo2, line1, line2, line3):
    if not connected.is_set():
        print("[ERRO] MQTT desconectado!")
        return
    payload = {
        "servo1": int(servo1),
        "servo2": int(servo2),
        "line1": line1,
        "line2": line2,
        "line3": line3,
    }
    message = json.dumps(payload, ensure_ascii=False)
    result = client.publish(
        TOPIC_COMMAND,
        message,
        qos=0,
        retain=False
    )
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print("[PYTHON] COMANDO ENVIADO")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("[ERRO] Falha ao publicar comando!")


# def menu():


#     while not connected.is_set():
#         time.sleep(0.2)
#     time.sleep(2)
#     while True:
#         l1 = input("Linha 1: ")
#         l2 = input("Linha 2: ")
#         l3 = input("Linha 3: ")
#         send_command(l1, l2, l3)


while True:
    try:
        print("[MQTT] Conectando...")
        client.connect(
            MQTT_SERVER,
            MQTT_PORT,
            keepalive=60
        )
        client.loop_start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrompido pelo usuario.")
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Cliente MQTT encerrado.")





