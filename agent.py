import requests
import os
import time
import subprocess

SERVIDOR = "http://IP_DO_SEU_SERVIDOR:5000"

MEDIA_DIR = "media"

os.makedirs(MEDIA_DIR, exist_ok=True)

ultimo_arquivo = None

while True:

    try:

        resposta = requests.get(
            f"{SERVIDOR}/api/comando",
            timeout=10
        )

        comando = resposta.json()

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