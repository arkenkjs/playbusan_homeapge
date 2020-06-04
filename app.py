from app import create_app
from app.models import db, User


app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User}

if __name__ == '__main__':
    app.run(port=5000, debug=True)