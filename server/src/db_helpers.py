from __future__ import annotations

from src import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    cookie = db.Column(db.String(255), nullable=True)


class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    challenge = db.Column(db.String(255), nullable=False)
    response = db.Column(db.String(255), nullable=False)


def as_dict(results: db.Model | list[db.Model]) -> dict | list[dict] | None:
    if not results:
        return None
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


def get_user_by_cookie(cookie: str) -> dict:
    user = User.query.filter_by(cookie=cookie).first()
    return as_dict(user)


def set_user_cookie(username: str, cookie: str) -> None:
    User.query.filter_by(username=username).update({'cookie': cookie})
    db.session.commit()


def get_user_challenges(user_id: int) -> list[dict[str, str]] | None:
    return as_dict(Challenge.query.filter_by(user_id=user_id).all())


def set_user_challenges(user_id: int, challenges: dict[str, str]) -> None:
    db.session.add_all([
        Challenge(user_id=user_id, challenge=challenge, response=response) for challenge, response in challenges.items()
    ])
    db.session.commit()


def remove_user_challenge(challenge_id: int) -> None:
    Challenge.query.filter_by(id=challenge_id).delete()
    db.session.commit()


def verify_challenge(user_id: int, challenge: str, response: str) -> dict[str, str]:
    return as_dict(Challenge.query.filter_by(user_id=user_id, challenge=challenge, response=response).first())
