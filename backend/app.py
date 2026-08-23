from flask import Flask, send_from_directory
from flask_cors import CORS
from routes import routes
import os

app = Flask(__name__)

CORS(app)

app.register_blueprint(routes)

FRONTEND_FOLDER = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend")
)

@app.route("/")
def home():
    return send_from_directory(
        FRONTEND_FOLDER,
        "dashboard.html"
    )

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )