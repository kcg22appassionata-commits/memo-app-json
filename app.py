from flask import Flask, render_template, request, jsonify
import json
import os

app = Flask(__name__)

MEMO_FILE = "memos.json"


# ---------- メモ読み込み ----------
def load_memos():
    if not os.path.exists(MEMO_FILE):
        return []
    with open(MEMO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------- メモ保存 ----------
def save_memos(memos):
    with open(MEMO_FILE, "w", encoding="utf-8") as f:
        json.dump(memos, f, ensure_ascii=False, indent=4)


@app.route("/")
def index():
    return render_template("index.html")


# ---------- メモ一覧取得 ----------
@app.route("/api/memos", methods=["GET"])
def api_get_memos():
    memos = load_memos()
    return jsonify(memos)


# ---------- メモ保存（新規 or 更新） ----------
@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.json
    memo_id = data.get("id")
    title = data.get("title")
    content = data.get("content")

    memos = load_memos()

    if memo_id is None:  
        # 新規メモ
        new_memo = {
            "id": int(__import__("time").time() * 1000),
            "title": title,
            "content": content
        }
        memos.insert(0, new_memo)
    else:
        # 編集（id一致するメモを更新）
        for m in memos:
            if m["id"] == memo_id:
                m["title"] = title
                m["content"] = content
                break

    save_memos(memos)
    return jsonify({"status": "ok"})


# ---------- メモ削除 ----------
@app.route("/api/delete", methods=["POST"])
def api_delete():
    data = request.json
    memo_id = data.get("id")

    memos = load_memos()
    memos = [m for m in memos if m["id"] != memo_id]
    save_memos(memos)

    return jsonify({"status": "ok"})


 #ローカル用if __name__ == "__main__":
   # app.run(debug=True)