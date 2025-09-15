import os
from datetime import timedelta

import html
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
    get_jwt,
)
from flask_jwt_extended.exceptions import JWTExtendedException
from models import PostModel, UserModel

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY", "your-super-secure-secret-key-change-in-production"
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
    minutes=15
)  # Короткое время жизни access token
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
    days=7
)  # Длинное время жизни refresh token
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
app.config["JWT_HEADER_NAME"] = "Authorization"
app.config["JWT_HEADER_TYPE"] = "Bearer"

jwt = JWTManager(app)

token_blacklist = set()


@app.before_request
def check_jwt():
    public_endpoints = ["/auth/login", "/api/health"]
    if request.path in public_endpoints:
        return

    if request.method == "OPTIONS":
        return

    try:
        verify_jwt_in_request()

        jwt_data = get_jwt()
        jti = jwt_data["jti"]
        if jti in token_blacklist:
            return jsonify({"error": "Token has been revoked"}), 401

    except JWTExtendedException as e:
        return jsonify({"error": "Invalid or expired token"}), 401
    except Exception as e:
        return jsonify({"error": "Authentication required"}), 401


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    return jwt_payload["jti"] in token_blacklist


def sanitize_output(data):
    if isinstance(data, str):
        return html.escape(data)
    elif isinstance(data, dict):
        return {k: sanitize_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    return data


@app.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json()

        if not data or "username" not in data or "password" not in data:
            return jsonify({"error": "Username and password required"}), 400

        username = data["username"].strip()[:50]
        password = data["password"][:100]

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        import time

        time.sleep(1)

        user = UserModel.authenticate(username, password)

        if user:
            access_token = create_access_token(
                identity=user["username"],
                additional_claims={"role": user["role"], "user_id": user["id"]},
            )

            refresh_token = create_refresh_token(
                identity=user["username"],
                additional_claims={"role": user["role"], "user_id": user["id"]},
            )

            return (
                jsonify(
                    {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "token_type": "bearer",
                        "expires_in": 900,  # 15 минут
                        "user": {
                            "username": user["username"],
                            "role": user["role"],
                            "user_id": user["id"],
                        },
                    }
                ),
                200,
            )

        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/profile", methods=["GET"])
@jwt_required()
def get_profile():
    try:
        user_data = UserModel.get_user_data(get_jwt_identity())
        if user_data:
            safe_profile = {
                "id": user_data["id"],
                "username": html.escape(user_data["username"]),
                "role": html.escape(user_data["role"]),
                "created_at": user_data["created_at"],
            }
            return jsonify(safe_profile), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    return (
        jsonify({"status": "healthy"}),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
