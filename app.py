import os
import uuid
from flask import Flask, render_template, request, jsonify, session
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

DATABASE_URL = os.environ.get("postgresql://memo_user:oPBFnhkqJ8M30m7qF5zZg9OwdKjStPqG@dpg-d4vre663jp1c73erbs8g-a/memo_db_f2im") # PostgreSQLの接続URL　環境変数


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL が未設定です")
    return psycopg.connect(
        DATABASE_URL,
        sslmode="require"
    )


def get_user_id():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    return session["user_id"]


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memos (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
            """)
        conn.commit()


@app.before_first_request
def startup():
    init_db()


@app.route("/")
def index():
    get_user_id()
    return render_template("index.html")


@app.route("/api/memos")
def get_memos():
    user_id = get_user_id()
    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, title, content FROM memos WHERE user_id=%s ORDER BY id DESC",
                (user_id,)
            )
            return jsonify(cur.fetchall())


@app.route("/api/save", methods=["POST"])
def save_memo():
    user_id = get_user_id()
    data = request.json or {}
    memo_id = data.get("id")
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    if not title or not content:
        return jsonify({"error": "title と content は必須"}), 400

    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if memo_id is None:
                cur.execute(
                    "INSERT INTO memos (user_id, title, content) VALUES (%s,%s,%s) RETURNING id,title,content",
                    (user_id, title, content)
                )
                memo = cur.fetchone()
            else:
                cur.execute(
                    """UPDATE memos
                       SET title=%s, content=%s, updated_at=NOW()
                       WHERE id=%s AND user_id=%s
                       RETURNING id,title,content""",
                    (title, content, memo_id, user_id)
                )
                memo = cur.fetchone()
                if memo is None:
                    return jsonify({"error": "更新対象が見つかりません"}), 404
        conn.commit()

    return jsonify({"ok": True, "memo": memo})


@app.route("/api/delete", methods=["POST"])
def delete_memo():
    user_id = get_user_id()
    memo_id = (request.json or {}).get("id")

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM memos WHERE id=%s AND user_id=%s",
                (memo_id, user_id)
            )
            if cur.rowcount == 0:
                return jsonify({"error": "削除対象なし"}), 404
        conn.commit()

    return jsonify({"ok": True})



 #ローカル用if __name__ == "__main__":
   # app.run(debug=True)