from flask import Flask
from datetime import timedelta
from extensions import db, jwt
from routes import api_bp
import json
def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    with open('config.json') as config_file:
        config = json.load(config_file)
        app.config.update(config)

    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(api_bp)

    return app
