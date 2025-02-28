# app.py

from flask import Flask, request
from config import Config
from extensions import db
from flask_migrate import Migrate
from services.auth_service import register_user, login_user
from flask_jwt_extended import JWTManager
from flask_cors import CORS

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)

# Initialize extensions
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    return register_user(data)

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    return login_user(data)

if __name__ == "__main__":
    app.run(debug=True)
