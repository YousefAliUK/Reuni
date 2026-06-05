"""
Reuni — Entry Point
Run this file to start the Flask development server.
Usage: python run.py
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False), port=5000)
