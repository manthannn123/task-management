import os
import time
from datetime import datetime

import mysql.connector
from mysql.connector import Error
from flask import Flask, jsonify, request

app = Flask(__name__)
ALLOWED_STATUSES = {"pending", "in_progress", "completed"}


def db_config():
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME", "task_manager"),
        "user": os.getenv("DB_USER", "taskapp"),
        "password": os.getenv("DB_PASSWORD", ""),
        "connection_timeout": 5,
    }


def get_connection(retries=5, delay=2):
    # Retry briefly while the database is starting.
    last_error = None
    for attempt in range(retries):
        try:
            return mysql.connector.connect(**db_config())
        except Error as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(delay)
    raise last_error


def serialize_row(row):
    if row is None:
        return None
    result = dict(row)
    for key in ("created_at", "updated_at"):
        value = result.get(key)
        if isinstance(value, datetime):
            result[key] = value.isoformat()
    return result


def fetch_tasks(task_id=None):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        if task_id is None:
            cursor.execute(
                "SELECT id, title, description, status, created_at, updated_at "
                "FROM tasks ORDER BY created_at DESC, id DESC"
            )
            return [serialize_row(row) for row in cursor.fetchall()]
        cursor.execute(
            "SELECT id, title, description, status, created_at, updated_at "
            "FROM tasks WHERE id = %s", (task_id,)
        )
        return serialize_row(cursor.fetchone())
    finally:
        cursor.close()
        connection.close()


@app.get("/api/health")
def health():
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        connection.close()
        return jsonify({"status": "ok", "database": "connected"}), 200
    except Error:
        app.logger.exception("Database health check failed")
        return jsonify({"status": "error", "database": "unavailable"}), 503


@app.get("/api/tasks")
def list_tasks():
    try:
        return jsonify(fetch_tasks()), 200
    except Error:
        app.logger.exception("Unable to list tasks")
        return jsonify({"error": "Database unavailable"}), 503


@app.get("/api/tasks/<int:task_id>")
def get_task(task_id):
    try:
        task = fetch_tasks(task_id)
        if task is None:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task), 200
    except Error:
        app.logger.exception("Unable to fetch task")
        return jsonify({"error": "Database unavailable"}), 503


@app.post("/api/tasks")
def create_task():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400

    title = data.get("title")
    description = data.get("description", "")
    status = data.get("status", "pending")

    if not isinstance(title, str) or not title.strip():
        return jsonify({"error": "Title is required"}), 400
    if len(title.strip()) > 200:
        return jsonify({"error": "Title must be 200 characters or fewer"}), 400
    if not isinstance(description, str):
        return jsonify({"error": "Description must be a string"}), 400
    if status not in ALLOWED_STATUSES:
        return jsonify({"error": "Invalid status"}), 400

    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, description, status) VALUES (%s, %s, %s)",
            (title.strip(), description.strip(), status),
        )
        task_id = cursor.lastrowid
        connection.commit()
        return jsonify(fetch_tasks(task_id)), 201
    except Error:
        if connection:
            connection.rollback()
        app.logger.exception("Unable to create task")
        return jsonify({"error": "Database unavailable"}), 503
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.put("/api/tasks/<int:task_id>")
def update_task(task_id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object"}), 400
    allowed_fields = {"title", "description", "status"}
    if not data or not set(data).issubset(allowed_fields):
        return jsonify({"error": "Provide title, description, and/or status only"}), 400

    try:
        current = fetch_tasks(task_id)
        if current is None:
            return jsonify({"error": "Task not found"}), 404

        title = data.get("title", current["title"])
        description = data.get("description", current["description"] or "")
        status = data.get("status", current["status"])
        if not isinstance(title, str) or not title.strip() or len(title.strip()) > 200:
            return jsonify({"error": "Title is required and must be 200 characters or fewer"}), 400
        if not isinstance(description, str):
            return jsonify({"error": "Description must be a string"}), 400
        if status not in ALLOWED_STATUSES:
            return jsonify({"error": "Invalid status"}), 400

        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE tasks SET title=%s, description=%s, status=%s WHERE id=%s",
                (title.strip(), description.strip(), status, task_id),
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()
        return jsonify(fetch_tasks(task_id)), 200
    except Error:
        app.logger.exception("Unable to update task")
        return jsonify({"error": "Database unavailable"}), 503


@app.delete("/api/tasks/<int:task_id>")
def delete_task(task_id):
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tasks WHERE id=%s", (task_id,))
        deleted = cursor.rowcount
        connection.commit()
        if not deleted:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"message": "Task deleted", "id": task_id}), 200
    except Error:
        if connection:
            connection.rollback()
        app.logger.exception("Unable to delete task")
        return jsonify({"error": "Database unavailable"}), 503
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(405)
def method_not_allowed(_error):
    return jsonify({"error": "Method not allowed"}), 405


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")
