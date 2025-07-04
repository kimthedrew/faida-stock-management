from app import db, User
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        db.create_all()
        # Create admin user
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Database initialized and admin user created.")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    from app import app
    init_db()