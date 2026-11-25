import json
import time
import threading
import requests
import paho.mqtt.client as mqtt


MQTT_SERVER = "broker.mqtt.cool"
MQTT_PORT = 1883

MQTT_ROOT = "mango/esp32c3/SA"


TOPIC_ALL = f"{MQTT_ROOT}/#"

# API FastAPI (python -m uvicorn api:app --reload)
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

#aqui é enviado o rfid para a api, que consulta o mysql. registra a mov e devolve os comandos dos servos e do display
def consultar_api(rfid, id_recinto):
    
    try:
        resposta = requests.post(URL_API, json={"uid": rfid, "id_recinto": id_recinto}, timeout=3)
        if resposta.status_code == 200:
            dados = resposta.json()
            print(f"[API] status: {dados.get('status')}")
            return (
                dados.get("servo1", 180),
                dados.get("servo2", 180),
                dados.get("line1", "Erro"),
                dados.get("line2", "Resposta API"),
                dados.get("line3", "Bloqueado")
            )
        print(f"[ERRO API] Status HTTP {resposta.status_code}: {resposta.text}")
    except Exception as err:
        print(f"[ERRO API] Falha ao comunicar com a API: {err}")

  #se der erro, ambas as travas fecham
    return 180, 180, "Erro de Sistema", "API Indisponivel", "Bloqueado"


def send_command(id_recinto, servo1, servo2, line1, line2, line3):
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
        f"{MQTT_ROOT}/{id_recinto}/command",
        message,
        qos=0,
        retain=False
    )
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"[PYTHON] COMANDO ENVIADO para a baia {id_recinto}")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("[ERRO] Falha ao publicar comando!")


def on_message(client, userdata, msg):
    topic = msg.topic
    # Ex.: mango/esp32c3/SA/1/rfid -> partes[3] = "1", partes[4] = "rfid"
    partes = topic.split("/")
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(f"\n[MQTT] {topic}: {msg.payload!r}")
        return
    print("\n" + "=" * 50)

    if len(partes) == 5 and partes[3].isdigit() and partes[4] == "rfid":
        id_recinto = int(partes[3])
        rfid = payload.get("uid")
        print(f"[ESP32 baia {id_recinto}] RFID")
        print(f"UID: {rfid}")

        if not rfid:
            print("[ERRO] Payload sem 'uid'.")
        else:
            servo1, servo2, line1, line2, line3 = consultar_api(rfid, id_recinto)
            send_command(id_recinto, servo1, servo2, line1, line2, line3)

    elif len(partes) == 5 and partes[4] == "command":
        print(f"[MQTT] COMANDO PUBLICADO (baia {partes[3]})")
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