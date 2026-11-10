import os
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "task-mysql"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER", "taskuser"),
    "password": os.getenv("DB_PASSWORD", "taskpass"),
    "database": os.getenv("DB_NAME", "taskdb"),
    "charset": "utf8mb4",
    "collation": "utf8mb4_0900_ai_ci",
    "connection_timeout": 5

}

STATUSES = ("대기", "진행 중", "완료")


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def response(data, status=200):
    return jsonify(data), status


@app.get("/health")
def health():
    try:
        with get_db() as conn:
            conn.ping(reconnect=False)
        return response({"status": "healthy", "database": "connected"})
    except mysql.connector.Error:
        return response({"status": "unhealthy"}, 503)


@app.get("/tasks")
def get_tasks():
    try:
        with get_db() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute("SELECT * FROM tasks ORDER BY id DESC")
                return response(cur.fetchall())
    except mysql.connector.Error:
        app.logger.exception("Task 조회 실패")
        return response({"error": "Database error"}, 500)


@app.get("/tasks/<int:task_id>")
def get_task(task_id):
    try:
        with get_db() as conn:
            with conn.cursor(dictionary=True) as cur:
                cur.execute(
                    "SELECT * FROM tasks WHERE id = %s",
                    (task_id,)
                )
                task = cur.fetchone()

        if not task:
            return response({"error": "Task not found"}, 404)

        return response(task)

    except mysql.connector.Error:
        app.logger.exception("Task 조회 실패")
        return response({"error": "Database error"}, 500)


@app.post("/tasks")
def create_task():
    data = request.get_json(silent=True) or {}

    title = data.get("title")
    description = data.get("description", "")
    status = data.get("status", "대기")

    if not isinstance(title, str) or not title.strip():
        return response({"error": "Title is required"}, 400)

    if not isinstance(description, str):
        return response({"error": "Invalid description"}, 400)

    if status not in STATUSES:
        return response({"error": "Invalid status"}, 400)

    if len(title.strip()) > 150 or len(description) > 2000:
        return response({"error": "Input too long"}, 400)

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tasks (title, description, status)
                    VALUES (%s, %s, %s)
                    """,
                    (title.strip(), description, status)
                )
                task_id = cur.lastrowid
            conn.commit()

        return response({"id": task_id, "message": "Task created"}, 201)

    except mysql.connector.Error:
        app.logger.exception("Task 등록 실패")
        return response({"error": "Database error"}, 500)


@app.put("/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True) or {}

    title = data.get("title")
    description = data.get("description", "")
    status = data.get("status", "대기")
    print(f"STATUS: {repr(status)}", flush=True)
    print(f"STATUS HEX: {status.encode('utf-8').hex()}", flush=True)

    if not isinstance(title, str) or not title.strip():
        return response({"error": "Title is required"}, 400)

    if not isinstance(description, str):
        return response({"error": "Invalid description"}, 400)

    if status not in STATUSES:
        return response({"error": "Invalid status"}, 400)

    if len(title.strip()) > 150 or len(description) > 2000:
        return response({"error": "Input too long"}, 400)

    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tasks
                    SET title = %s, description = %s, status = %s
                    WHERE id = %s
                    """,
                    (title.strip(), description, status, task_id)
                )

                if cur.rowcount == 0:
                    cur.execute(
                        "SELECT id FROM tasks WHERE id = %s",
                        (task_id,)
                    )
                    if not cur.fetchone():
                        return response({"error": "Task not found"}, 404)

            conn.commit()

        return response({"message": "Task updated"})

    except mysql.connector.Error:
        app.logger.exception("Task 수정 실패")
        return response({"error": "Database error"}, 500)


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM tasks WHERE id = %s",
                    (task_id,)
                )

                if cur.rowcount == 0:
                    return response({"error": "Task not found"}, 404)

            conn.commit()

        return response({"message": "Task deleted"})

    except mysql.connector.Error:
        app.logger.exception("Task 삭제 실패")
        return response({"error": "Database error"}, 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
