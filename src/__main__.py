import argparse

from waitress import serve

from . import create_app


def main():
    parser = argparse.ArgumentParser(description="Run the ADR4agents API with Waitress.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)
    arguments = parser.parse_args()
    if not 1 <= arguments.port <= 65535:
        parser.error("Port must be between 1 and 65535.")
    app = create_app()
    serve(app, host=arguments.host, port=arguments.port,
          max_request_body_size=app.config["MAX_CONTENT_LENGTH"])


if __name__ == "__main__":
    main()
