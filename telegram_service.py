import requests


TOKEN = "8213206313:AAGDWWoS0mSV0hzKpN8evVyxhokIQrFbbZw"

CHAT_ID = "-5572570999"


def enviar(mensagem):

    requests.post(

        f"https://api.telegram.org/bot{TOKEN}/sendMessage",

        data={

            "chat_id": CHAT_ID,

            "text": mensagem

        }

    )