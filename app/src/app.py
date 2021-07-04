from flask import Flask, request


app = Flask(__name__)


def check_auth():
    if "X-UserId" not in request.headers:
        return "Not authenticated"


@app.route("/users/me")
def me():
    check_auth()

    return {
        "id": request.headers["X-UserId"],
        "login": request.headers["X-User"],
        "email": request.headers["X-Email"],
        "first_name": request.headers["X-First-Name"],
        "last_name": request.headers["X-Last-Name"],
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="80", debug=True)
