from flask import Flask, jsonify
import socket
import os
import time
import random

app = Flask(__name__)
# Simulated database connection flag (for demo)
DB_CONNECTED = False
@app.route("/health/live", methods=["GET"])
def health_live():
    """Liveness check — container is running"""
    return jsonify({
        "status": "alive",
        "service": os.getenv("SERVICE_NAME", "microservice"),
        "hostname": socket.gethostname()
    }), 200

@app.route("/health/ready", methods=["GET"])
def health_ready():
    """Readiness check — verifies dependencies like DB or cache"""
    global DB_CONNECTED

    # For real apps: Replace this with an actual DB/ping check
    # Example:
    # try:
    #     conn = psycopg2.connect(os.getenv("DATABASE_URL"), connect_timeout=2)
    #     conn.close()
    # except Exception as e:
    #     return jsonify({"status": "not_ready", "error": str(e)}), 503

    # Simulated DB readiness
    if not DB_CONNECTED:
        # Simulate connecting after startup delay
        if random.random() > 0.5:
            DB_CONNECTED = True
        else:
            return jsonify({"status": "not_ready", "reason": "DB not connected yet"}), 503

    return jsonify({
        "status": "ready",
        "service": os.getenv("SERVICE_NAME", "microservice"),
        "hostname": socket.gethostname()
    }), 200


if __name__ == "__main__":
    # Simulate startup delay for DB connection
    time.sleep(3)
    print("Starting service...")

    app.run(host="0.0.0.0", port=8082)