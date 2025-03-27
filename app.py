from flask import Flask
from flask_login import LoginManager
from application.database import db
from application.models import User, Admin  

def create_app():
    app = Flask(__name__)
    app.debug = True
    app.config['SECRET_KEY'] = 'secretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///quizdata.sqlite3"

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        db.create_all()

        # Ensure at least one admin user exists
        if not User.query.filter_by(user_role=0).first():
            admin_user = User(username="admin", user_role=0)
            db.session.add(admin_user)
            db.session.commit()

            db.session.add(Admin(username="admin", passwd="admin123", id=admin_user.id))
            db.session.commit()

    # Setup Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "admin_login"  # Redirect unauthenticated users to admin login

    @login_manager.user_loader
    def load_user(user_id):
    # Try to load the user as an Admin first
        admin = Admin.query.get(int(user_id))
        if admin:
            return admin  # ✅ Now returns an Admin instance

        # If not an admin, load as a normal User
        user = User.query.get(int(user_id))
        return user


    return app


app = create_app()

# Import routes after app is created
from application.routes import *  

if __name__ == "__main__":
    app.run()
