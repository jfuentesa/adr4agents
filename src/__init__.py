from flask import Flask

from .api import blueprint
from .config import load_config
from .db import close_db, initialize_database
from .http_errors import register_handlers
from .web import blueprint as web_blueprint


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(load_config())
    if config is not None:
        app.config.update(config)
    app.json.sort_keys = False
    initialize_database(app.config["DATABASE"])
    app.teardown_appcontext(close_db)
    app.register_blueprint(blueprint)
    app.register_blueprint(web_blueprint)
    register_handlers(app)
    return app
