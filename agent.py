import requests
import os
import time
import subprocess
import socket
import psutil
import json

SERVIDOR = "http://IP_DO_SEU_SERVIDOR:5000"

MEDIA_DIR = "media"

os.makedirs(MEDIA_DIR, exist_ok=True)

ultimo_arquivo = None

def get_hostname():
    return socket.gethostname()


def get_cpu():
    return psutil.cpu_percent(interval=1)


def get_memoria():
    return psutil.virtual_memory().percent


def get_disco():
    return psutil.disk_usage("/").percent


def get_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Desconhecido"


def get_gateway():

    try:

        gateway = subprocess.check_output(
            "ip route | grep default | awk '{print $3}'",
            shell=True
        ).decode().strip()

        return gateway

    except:
        return "Desconhecido"


def get_uptime():

    segundos = int(time.time() - psutil.boot_time())

    dias = segundos // 86400
    horas = (segundos % 86400) // 3600
    minutos = (segundos % 3600) // 60

    return f"{dias}d {horas}h {minutos}min"


def get_resolucao():

    try:

        resultado = subprocess.check_output(
            "xrandr | grep '*' | head -n1",
            shell=True
        ).decode()

        return resultado.split()[0]

    except:

        return "Desconhecida"


def get_anydesk():

    try:

        numero = subprocess.check_output(
            "anydesk --get-id",
            shell=True
        ).decode().strip()

        return numero

    except:

        return "Não instalado"


def get_ip_publico():

    try:

        return requests.get(
            "https://api.ipify.org",
            timeout=5
        ).text

    except:

        return "Desconhecido"
    
def enviar_status():

    dados = {

        "hostname": get_hostname(),

        "status": "online",

        "arquivo": ultimo_arquivo,

        "uptime": get_uptime(),

        "ip_local": get_ip_local(),

        "gateway": get_gateway(),

        "ip_publico": get_ip_publico(),

        "cpu": get_cpu(),

        "memoria": get_memoria(),

        "disco": get_disco(),

        "anydesk": get_anydesk(),

        "resolucao": get_resolucao()

    }

    try:

        requests.post(
            f"{SERVIDOR}/api/status",
            json=dados,
            timeout=10
        )

    except Exception as e:

        print("Erro enviando status:", e)

while True:

    try:

        resposta = requests.get(
            f"{SERVIDOR}/api/comando",
            timeout=10
        )

        comando = resposta.json()

        enviar_status()

        if comando["acao"] == "stop":

            subprocess.run(
            ["pkill", "mpv"],
            stderr=subprocess.DEVNULL
        )

            subprocess.run(
            ["pkill", "feh"],
            stderr=subprocess.DEVNULL
        )

        ultimo_arquivo = None

        print("Reprodução parada")

        if comando["acao"] == "play":

            arquivo = comando["arquivo"]
            tipo = comando["tipo"]

            if arquivo != ultimo_arquivo:

                print(f"Novo arquivo: {arquivo}")

                url = (
                    f"{SERVIDOR}/download/"
                    f"{tipo}/{arquivo}"
                )

                destino = os.path.join(
                    MEDIA_DIR,
                    arquivo
                )

                r = requests.get(url)

                with open(destino, "wb") as f:
                    f.write(r.content)

                subprocess.run(
                    ["pkill", "mpv"],
                    stderr=subprocess.DEVNULL
                )

                subprocess.run(
                    ["pkill", "feh"],
                    stderr=subprocess.DEVNULL
                )

                if tipo == "video":

                    subprocess.Popen([
                        "mpv",
                        "--fs",
                        "--loop-file=inf",
                        destino
                    ])

                else:

                    subprocess.Popen([
                        "feh",
                        "--fullscreen",
                        destino
                    ])

                ultimo_arquivo = arquivo

    except Exception as e:

        print(e)

    time.sleep(5)