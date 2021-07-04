import os

from flask import Flask, request, abort
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

config = {
    "DATABASE_URI": os.environ.get("DATABASE_URI", ""),
}

engine = create_engine(config["DATABASE_URI"], echo=True)

SESSIONS = {}


NOT_AUTHENTICATED_RESPONSE = {"message": "Please go to login and provide Login/Password"}, 401


def generate_session_id(size=40):
    import string
    import random

    chars = string.ascii_uppercase + string.digits + string.ascii_lowercase
    return "".join(random.choice(chars) for _ in range(size))


def create_session(data):
    session_id = generate_session_id()
    SESSIONS[session_id] = data
    return session_id


def register_user(login, password, email, first_name, last_name):
    try:
        with engine.connect() as connection:
            result = connection.execute(
                """
                insert into auth_user (login, password, email, first_name, last_name)
                values ('{}', '{}', '{}', '{}', '{}') returning id;
                """.format(
                    login, password, email, first_name, last_name
                )
            ).first()
            id_ = result["id"]
        return {"id": id_}
    except IntegrityError:
        abort(400, "login/email already exists")


def get_user_by_credentials(login, password):
    with engine.connect() as connection:
        result = connection.execute(
            "select id, login, email, first_name, last_name from auth_user "
            "where login='{}' and password='{}'".format(login, password)
        )
        rows = [dict(r.items()) for r in result]
    return rows[0]


def update_profile(profile_id, email, first_name, last_name):
    update_attrs = []
    if email:
        update_attrs.append("email='{}'".format(email))
    if first_name:
        update_attrs.append("first_name='{}'".format(first_name))
    if last_name:
        update_attrs.append("last_name='{}'".format(last_name))

    if update_attrs:
        update_attrs_sql = ", ".join(update_attrs)
    else:
        return {}

    try:
        with engine.connect() as connection:
            connection.execute(
                """
                update auth_user
                set {}
                where id='{}';
                """.format(
                    update_attrs_sql, profile_id
                )
            )

        return get_user_by_id(profile_id)

    except IntegrityError:
        abort(400, "email already exists")


def get_user_by_id(profile_id):
    with engine.connect() as connection:
        result = connection.execute(
            "select id, login, email, first_name, last_name from auth_user "
            "where id='{}'".format(profile_id)
        )
        rows = [dict(r.items()) for r in result]

    return rows[0]


@app.route("/sessions", methods=["GET"])
def sessions():
    return SESSIONS


@app.route("/register", methods=["POST"])
def register():
    request_data = request.get_json()
    # add validation
    login = request_data["login"]
    password = request_data["password"]
    email = request_data["email"]
    first_name = request_data["first_name"]
    last_name = request_data["last_name"]

    return register_user(login, password, email, first_name, last_name)


@app.route("/login", methods=["POST"])
def login():
    request_data = request.get_json()
    login = request_data["login"]
    password = request_data["password"]
    user_info = get_user_by_credentials(login, password)

    if user_info:
        session_id = create_session(user_info)
        response = app.make_response({"status": "ok"})
        response.set_cookie("session_id", session_id, httponly=True)

        return response
    else:
        abort(401)


@app.route("/signin", methods=["GET"])
def signin():
    return NOT_AUTHENTICATED_RESPONSE


@app.route("/auth")
def auth():
    if "session_id" in request.cookies:
        session_id = request.cookies["session_id"]
        if session_id in SESSIONS:
            data = SESSIONS[session_id]
            response = app.make_response(data)
            response.headers["X-UserId"] = data["id"]
            response.headers["X-User"] = data["login"]
            response.headers["X-Email"] = data["email"]
            response.headers["X-First-Name"] = data["first_name"]
            response.headers["X-Last-Name"] = data["last_name"]

            return response

    abort(401)


@app.route("/logout", methods=["GET", "POST"])
def logout():
    response = app.make_response({"status": "ok"})
    response.set_cookie("session_id", "", expires=0)

    return response


@app.route("/profile", methods=["PATCH"])
def update():

    if "session_id" in request.cookies:
        session_id = request.cookies["session_id"]
        if session_id in SESSIONS:
            data = SESSIONS[session_id]
            response = app.make_response(data)
            response.headers["X-UserId"] = data["id"]

            request_data = request.get_json()

            updated_profile = update_profile(
                data["id"],
                request_data.get("email"),
                request_data.get("first_name"),
                request_data.get("last_name")
            )

            SESSIONS[session_id] = get_user_by_id(data["id"])

            return updated_profile

    return NOT_AUTHENTICATED_RESPONSE


@app.route("/health")
def health():
    return {"status": "OK"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="80", debug=True)
