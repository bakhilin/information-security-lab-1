from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from datetime import timedelta
from dotenv import load_dotenv
import os
from models import UserModel, PostModel

load_dotenv()

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)


@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"error": "Username and password required"}), 400
        
        user = UserModel.authenticate(data['username'], data['password'])
        
        if user:
            access_token = create_access_token(
                identity=user['username'],
                additional_claims={"role": user["role"]}
            )
            
            return jsonify({
                "access_token": access_token,
                "user": {
                    "username": user['username'],
                    "role": user['role']
                }
            }), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/data', methods=['GET'])
@jwt_required()
def get_data():
    try:
        data_type = request.args.get('type', 'posts')
        
        if data_type == 'posts':
            posts = PostModel.get_all_posts()
            return jsonify({
                "data": posts,
                "count": len(posts),
                "requested_by": get_jwt_identity()
            }), 200
            
        elif data_type == 'users':
            from flask_jwt_extended import get_jwt
            if get_jwt()['role'] != 'admin':
                return jsonify({"error": "Admin access required"}), 403
                
            users = UserModel.get_all_users()
            return jsonify({
                "users": users,
                "count": len(users)
            }), 200
            
        else:
            return jsonify({"error": "Invalid data type"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_data = UserModel.get_user_data(get_jwt_identity())
        return jsonify(user_data) if user_data else jsonify({"error": "User not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({"error": "Title and content required"}), 400
        
        post_id = PostModel.create_post(
            data['title'], 
            data['content'], 
            get_jwt_identity()
        )
        
        return jsonify({
            "message": "Post created successfully",
            "post_id": post_id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy", 
        "service": "Flask API",
        "database": "SQLite3"
    }), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)