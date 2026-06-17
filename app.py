from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def init_db():
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


@app.route("/")
def index():

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM videos")
    videos = cursor.fetchall()

    conn.close()

    return render_template("index.html", videos=videos)


@app.route("/upload", methods=["POST"])
def upload():

    arquivo = request.files["video"]

    if arquivo:

        caminho = os.path.join(
            app.config["UPLOAD_FOLDER"],
            arquivo.filename
        )

        arquivo.save(caminho)

        conn = sqlite3.connect("banco.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO videos(nome) VALUES(?)",
            (arquivo.filename,)
        )

        conn.commit()
        conn.close()

    return redirect(url_for("index"))


@app.route("/delete/<int:id>")
def delete(id):

    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT nome FROM videos WHERE id=?",
        (id,)
    )

    video = cursor.fetchone()

    if video:

        arquivo = os.path.join(
            app.config["UPLOAD_FOLDER"],
            video[0]
        )

        if os.path.exists(arquivo):
            os.remove(arquivo)

    cursor.execute(
        "DELETE FROM videos WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("templates/index.html"))


if __name__ == "__main__":

    init_db()

    app.run(
        host="0.0.0.0",
        port=5000
    )