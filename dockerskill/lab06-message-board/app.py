import os
from contextlib import closing

import pymysql
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Lab 06 留言板</title>
</head>
<body>
  <h1>Lab 06 留言板</h1>
  <form method="post">
    <input name="message" maxlength="200" required placeholder="输入留言">
    <button type="submit">提交</button>
  </form>
  <ul>
  {% for message in messages %}
    <li>{{ message }}</li>
  {% else %}
    <li>还没有留言</li>
  {% endfor %}
  </ul>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def board():
    message = request.form.get("message", "").strip()
    if request.method == "POST" and not 1 <= len(message) <= 200:
        return "留言长度必须为 1 到 200 个字符", 400

    with closing(pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        connect_timeout=5,
    )) as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    body VARCHAR(200) NOT NULL
                )
            """)

            if request.method == "POST":
                cursor.execute("INSERT INTO messages (body) VALUES (%s)", (message,))
                connection.commit()
                return redirect(url_for("board"))

            cursor.execute("SELECT body FROM messages ORDER BY id DESC")
            messages = [row[0] for row in cursor.fetchall()]

    return render_template_string(PAGE, messages=messages)