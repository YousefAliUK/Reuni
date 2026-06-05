from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    email = "19284815@brookes.ac.uk"
    u = User.query.filter_by(email=email).first()
    if not u:
        print(f"User {email} not found. Creating a new admin account...")
        u = User(
            email=email,
            name="Yousef (Admin)",
            is_verified=True,
            is_active=True,
            role="admin",
            university_domain="brookes.ac.uk"
        )
        u.set_password("password123")
        db.session.add(u)
    else:
        print(f"User {email} found. Promoting to admin...")
        u.role = "admin"
        u.is_active = True
        u.is_verified = True
        
    db.session.commit()
    print("Success! Admin account is set up and active.")
    print("Email: 19284815@brookes.ac.uk")
    print("Password: password123")
