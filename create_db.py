if __name__ == '__main__':
    
    from app import create_app, db
    from app.models import *

    app = create_app()
    app.app_context().push()
    db.create_all()