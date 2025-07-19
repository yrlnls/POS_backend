# seed.py
from app import app, db
from models import User

def seed():
    with app.app_context():
        db.create_all()
        if not User.query.first():  # Avoid duplicates
            admin = User(username='admin', email='admin@example.com', role='admin')
            admin.set_password('admin123')
            user1 = User(username='user1', email='user1@example.com', role='user')
            user1.set_password('pass123')
            user2 = User(username='user2', email='user2@example.com', role='user')
            user2.set_password('pass123')

            db.session.add_all([admin, user1, user2])
            db.session.commit()

            print("Database seeded!")

if __name__ == '__main__':
    seed()