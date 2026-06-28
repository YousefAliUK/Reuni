"""
Reuni — Entry Point
Run this file to start the Flask development server.
Usage: python run.py
"""

from app import create_app, db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=app.config.get("DEBUG", False), port=5000)
