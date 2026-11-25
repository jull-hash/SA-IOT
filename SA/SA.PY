import json
import time
import threading
import requests
import paho.mqtt.client as mqtt


MQTT_SERVER = "broker.mqtt.cool"
MQTT_PORT = 1883

MQTT_ROOT = "mango/esp32c3/SA"

TOPIC_RFID = f"{MQTT_ROOT}/rfid"
TOPIC_COMMAND = f"{MQTT_ROOT}/command"
TOPIC_ALL = f"{MQTT_ROOT}/#"

# API FastAPI (python -m uvicorn main:app --reload)
URL_API = "http://localhost:8000/api/validar-rfid"

CLIENT_ID = "Python-Client-juliana"

connected = threading.Event()

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id=CLIENT_ID
)


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


def consultar_api(rfid):
    """
    Envia o RFID para a API, que consulta o MySQL, registra
    entrada/saida e devolve os comandos dos servos e do display.
    """
    try:
        resposta = requests.post(URL_API, json={"uid": rfid}, timeout=3)
        if resposta.status_code == 200:
            dados = resposta.json()
            print(f"[API] status: {dados.get('status')}")
            return (
                dados.get("servo1", 0),
                dados.get("servo2", 0),
                dados.get("line1", "Erro"),
                dados.get("line2", "Resposta API"),
                dados.get("line3", "Bloqueado")
            )
        print(f"[ERRO API] Status HTTP {resposta.status_code}")
    except Exception as err:
        print(f"[ERRO API] Falha ao comunicar com a API: {err}")

    # Em caso de falha, mantem a trava fechada (RF007)
    return 0, 0, "Erro de Sistema", "API Indisponivel", "Bloqueado"


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


def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"\n[MQTT] {topic}: {msg.payload!r}")
        return
    print("\n" + "=" * 50)

    if topic == TOPIC_RFID:
        rfid = payload.get("uid")
        print("[ESP32] RFID")
        print(f"UID: {rfid}")

        if not rfid:
            print("[ERRO] Payload sem 'uid'.")
        else:
            servo1, servo2, line1, line2, line3 = consultar_api(rfid)
            send_command(servo1, servo2, line1, line2, line3)

    elif topic == TOPIC_COMMAND:
        print("[MQTT] COMANDO PUBLICADO")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"[MQTT] Topico: {topic}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    print("=" * 50)


client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message


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
        break
    except Exception as e:
        print(f"Erro: {e}")
        time.sleep(5)
    finally:
        client.loop_stop()
        client.disconnect()
        print("Cliente MQTT encerrado.")