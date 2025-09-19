import json
from app import create_app
from extensions import db
from flask_jwt_extended import create_access_token

def setup_app():
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite://",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY="test-secret",
    )
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


def test_happy_flow():
    app = setup_app()
    client = app.test_client()

    # 1) register
    r = client.post("/register", json={"username": "alice", "password": "Secret123"})
    assert r.status_code == 201

    # 2) login -> token
    r = client.post("/login", json={"username": "alice", "password": "Secret123"})
    assert r.status_code == 200
    token = r.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3) create task
    r = client.post("/createTask", json={"title": "Write docs", "completed": False}, headers=headers)
    assert r.status_code == 201
    task = r.get_json()
    tid = task["id"]
    assert task["title"] == "Write docs"
    assert task["completed"] is False

    # 4) list tasks (no filters)
    r = client.get("/getAllTasks", headers=headers)
    assert r.status_code == 200
    tasks = r.get_json()
    assert len(tasks) == 1

    # 5) get by id
    r = client.get(f"/getTask/{tid}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["id"] == tid

    # 6) update task -> completed true
    r = client.put(f"/updateTask/{tid}", json={"completed": True}, headers=headers)
    assert r.status_code == 200
    assert r.get_json()["completed"] is True

    # 7) delete
    r = client.delete(f"/deleteTask/{tid}", headers=headers)
    assert r.status_code == 200

def test_basic_validation_and_filters():
    app = setup_app()
    client = app.test_client()

    # register + login
    client.post("/register", json={"username": "bob", "password": "Secret123"})
    r = client.post("/login", json={"username": "bob", "password": "Secret123"})
    token = r.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # create validation: missing title
    r = client.post("/createTask", json={"completed": True}, headers=headers)
    assert r.status_code == 400

    # create a few tasks
    client.post("/createTask", json={"title": "t1"}, headers=headers)
    client.post("/createTask", json={"title": "t2"}, headers=headers)
    client.post("/createTask", json={"title": "t3", "completed": True}, headers=headers)

    # pagination
    r = client.get("/getAllTasks?page=1&limit=2", headers=headers)
    assert r.status_code == 200
    assert len(r.get_json()) == 2

    r = client.get("/getAllTasks?page=2&limit=2", headers=headers)
    assert r.status_code == 200
    assert len(r.get_json()) == 1

    r = client.get("/getAllTasks?status=completed", headers=headers)
    assert r.status_code == 200
    assert all(t["completed"] is True for t in r.get_json())

    r = client.get("/getAllTasks?status=pending", headers=headers)
    assert r.status_code == 200
    assert all(t["completed"] is False for t in r.get_json())

def test_auth_required():
    app = setup_app()
    client = app.test_client()

    # creating without token should fail
    r = client.post("/createTask", json={"title": "x"})
    assert r.status_code in (401, 422)
