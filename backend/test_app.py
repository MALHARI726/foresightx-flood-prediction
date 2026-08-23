from flask import Flask
app = Flask(__name__)

@app.route("/status")
def status():
    return {"message": "Backend is running!"}

if __name__ == "__main__":
    app.run(debug=True)
