from app import db, User
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        db.create_all()
        # Create admin user
        if not User.query.filter_by(username='shem').first():
            staff = User(
                username='shem',
                password=generate_password_hash('123456'),
                role='staff'
            )
            db.session.add(staff)
            db.session.commit()
            print("Database initialized and staff user created.")
        else:
            print("staff user already exists.")

if __name__ == '__main__':
    from app import app
    init_db()