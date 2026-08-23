import types
import blinker

# Create a dummy Namespace class so Flask can start
class DummyNamespace:
    def signal(self, name, doc=None):
        return lambda *a, **kw: None

blinker.Namespace = DummyNamespace

from flask import Flask
from flask_cors import CORS

from routes import routes


app = Flask(__name__)

CORS(app)

app.register_blueprint(routes)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )