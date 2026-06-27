from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask import send_from_directory
import sqlite3
import os
from telegram_service import enviar

app = Flask(__name__)

app.secret_key = "sua_chave_secreta"

# Limite de 500 MB
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

VIDEO_FOLDER = "uploads/videos"
IMAGE_FOLDER = "uploads/imagens"

os.makedirs(VIDEO_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {
    "mp4",
    "mov",
    "avi",
    "mkv",
    "webm",
    "jpg",
    "jpeg",
    "png",
    "gif"
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_file_type(filename):
    ext = filename.rsplit(".", 1)[1].lower()

    if ext in ["mp4", "mov", "avi", "mkv", "webm"]:
        return "video"

    return "imagem"


def init_db():
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS arquivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL
        )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS comandos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        acao TEXT,
        arquivo TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dispositivos (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            hostname TEXT UNIQUE,

            status TEXT,

            arquivo TEXT,

            uptime TEXT,

            ip_local TEXT,

            gateway TEXT,

            ip_publico TEXT,

            cpu REAL,

            memoria REAL,

            disco REAL,

            anydesk TEXT,

            resolucao TEXT,

            ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP

            )
        """)

    conn.commit()
    conn.close()


@app.route("/")
def index():

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM arquivos
        ORDER BY id DESC
    """)

    arquivos = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM dispositivos
        ORDER BY hostname
    """)

    dispositivos = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        arquivos=arquivos,
        dispositivos=dispositivos
    )


@app.route("/upload", methods=["POST"])
def upload():

    if "arquivo" not in request.files:
        flash("Nenhum arquivo enviado.")
        return redirect(url_for("index"))

    arquivo = request.files["arquivo"]

    if arquivo.filename == "":
        flash("Nenhum arquivo selecionado.")
        return redirect(url_for("index"))

    if not allowed_file(arquivo.filename):
        flash("Formato não permitido.")
        return redirect(url_for("index"))

    tipo = get_file_type(arquivo.filename)

    if tipo == "video":
        caminho = os.path.join(
            VIDEO_FOLDER,
            arquivo.filename
        )
    else:
        caminho = os.path.join(
            IMAGE_FOLDER,
            arquivo.filename
        )

    arquivo.save(caminho)

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO arquivos(nome, tipo) VALUES(?, ?)",
        (arquivo.filename, tipo)
    )

    conn.commit()
    conn.close()

    flash("Upload realizado com sucesso!")

    return redirect(url_for("index"))


@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT nome, tipo FROM arquivos WHERE id=?",
        (id,)
    )

    arquivo = cursor.fetchone()

    if arquivo:

        nome, tipo = arquivo

        pasta = VIDEO_FOLDER if tipo == "video" else IMAGE_FOLDER

        caminho = os.path.join(
            pasta,
            nome
        )

        if os.path.exists(caminho):
            os.remove(caminho)

        cursor.execute(
            "DELETE FROM arquivos WHERE id=?",
            (id,)
        )

        conn.commit()

    conn.close()

    return redirect(url_for("index"))


@app.errorhandler(413)
def arquivo_grande(e):
    return "Arquivo maior que 500 MB.", 413

# Rota para comando de reproduzir midia na TV
@app.route("/play/<int:id>")
def play(id):

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT nome FROM arquivos WHERE id=?",
        (id,)
    )

    arquivo = cursor.fetchone()

    if arquivo:

        cursor.execute("DELETE FROM comandos")

        cursor.execute(
            "INSERT INTO comandos (acao, arquivo) VALUES (?, ?)",
            ("play", arquivo[0])
        )

        conn.commit()

    conn.close()

    flash("Comando enviado para a TV.")

    return redirect("/")
# Comando para criar a API de comando para reproduzir midia na TV
@app.route("/api/comando")
def api_comando():

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT acao, arquivo
        FROM comandos
        ORDER BY id DESC
        LIMIT 1
    """)

    comando = cursor.fetchone()

    conn.close()

    if not comando:
        return jsonify({
            "acao": "nenhuma"
        })

    acao = comando[0]
    arquivo = comando[1]

    if acao == "stop":
        return jsonify({
            "acao": "stop"
        })

    extensao = arquivo.rsplit(".", 1)[1].lower()

    if extensao in ["mp4", "avi", "mov", "mkv", "webm"]:
        tipo = "video"
    else:
        tipo = "imagem"

    return jsonify({
        "acao": acao,
        "arquivo": arquivo,
        "tipo": tipo
    })

@app.route("/download/<tipo>/<nome>")
def download(tipo, nome):

    if tipo == "video":
        return send_from_directory(
            VIDEO_FOLDER,
            nome,
            as_attachment=True
        )

    if tipo == "imagem":
        return send_from_directory(
            IMAGE_FOLDER,
            nome,
            as_attachment=True
        )

    return "Arquivo não encontrado", 404

@app.route("/stop")
def stop():

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM comandos")

    cursor.execute(
        "INSERT INTO comandos (acao, arquivo) VALUES (?, ?)",
        ("stop", "")
    )

    conn.commit()
    conn.close()

    flash("Comando de parada enviado.")

    return redirect("/")

@app.route("/api/status", methods=["POST"])
def api_status():

    dados = request.json

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM dispositivos
        WHERE hostname=?
    """, (dados["hostname"],))

    existe = cursor.fetchone()

    if existe:

        cursor.execute("""

            UPDATE dispositivos

            SET

                status=?,
                arquivo=?,
                uptime=?,
                ip_local=?,
                gateway=?,
                ip_publico=?,
                cpu=?,
                memoria=?,
                disco=?,
                anydesk=?,
                resolucao=?,
                ultima_atualizacao=CURRENT_TIMESTAMP

            WHERE hostname=?

        """, (

            dados["status"],
            dados["arquivo"],
            dados["uptime"],
            dados["ip_local"],
            dados["gateway"],
            dados["ip_publico"],
            dados["cpu"],
            dados["memoria"],
            dados["disco"],
            dados["anydesk"],
            dados["resolucao"],
            dados["hostname"]

        ))

    else:

        cursor.execute("""

            INSERT INTO dispositivos (

                hostname,
                status,
                arquivo,
                uptime,
                ip_local,
                gateway,
                ip_publico,
                cpu,
                memoria,
                disco,
                anydesk,
                resolucao

            )

            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)

        """, (

            dados["hostname"],
            dados["status"],
            dados["arquivo"],
            dados["uptime"],
            dados["ip_local"],
            dados["gateway"],
            dados["ip_publico"],
            dados["cpu"],
            dados["memoria"],
            dados["disco"],
            dados["anydesk"],
            dados["resolucao"]

        ))

    conn.commit()
    conn.close()

    return jsonify({
        "status":"ok"
    })

@app.route("/telegram/<int:id>")
def telegram(id):

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""

        SELECT *

        FROM dispositivos

        WHERE id=?

    """,(id,))

    tv = cursor.fetchone()

    conn.close()

    if not tv:

        flash("TV não encontrada.")

        return redirect("/")

    mensagem = f"""

📺 {tv[1]}

🟢 Status:
{tv[2]}

🎬 Arquivo:
{tv[3]}

⏱ Tempo ligado:
{tv[4]}

🌐 IP Local:
{tv[5]}

🚪 Gateway:
{tv[6]}

🌍 IP Público:
{tv[7]}

🧠 CPU:
{tv[8]}%

💾 RAM:
{tv[9]}%

📦 Disco:
{tv[10]}%

🖥 Resolução:
{tv[12]}

🆔 AnyDesk:
{tv[11]}

"""

    enviar(mensagem)

    flash("Informações enviadas ao Telegram.")

    return redirect("/")

if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )