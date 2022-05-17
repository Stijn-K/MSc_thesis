from __future__ import annotations

from src import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    credentials_id = db.Column(db.String(255), nullable=True)


def as_dict(results: db.Model | list[db.Model]) -> dict | list[dict]:
    if not results:
        return {}
    elif isinstance(results, list):
        return [{column: str(getattr(row, column)) for column in row.__table__.c.keys()} for row in results]
    else:
        return {column: str(getattr(results, column)) for column in results.__table__.c.keys()}


def initialize_db() -> None:
    tables = db.engine.table_names()
    for table in tables:
        db.engine.execute(f'DROP TABLE {table} CASCADE')

    db.create_all()
    db.session.add(User(username='test_user', password='12345'))
    db.session.commit()


def get_user_by_credentials(username: str, password: str) -> dict:
    user = User.query.filter_by(username=username, password=password).first()
    return as_dict(user)


def set_user_credentials_id(username: str, cid: str) -> None:
    User.query.filter_by(username=username).update({'credentials_id': cid})
    db.session.commit()


def get_user_by_credentials_id(cid: str) -> dict:
    return as_dict(User.query.filter_by(credentials_id=cid).first())
