from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user, UserMixin, login_user, logout_user

import secrets


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['REMEMBER_COOKIE_SECURE'] = False
app.config['REMEMBER_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.secret_key = secrets.token_hex()
login_manager = LoginManager()
login_manager.session_protection = None
login_manager.login_view = 'login'
login_manager.init_app(app)


_FINGERPRINT = False


def is_authenticated(current_user, fingerprint):
    if not current_user.is_anonymous:
        if not current_user.is_authenticated:
            flash('You are not authenticated!', 'danger')
            return False
        if _FINGERPRINT and not current_user.fingerprint == str(fingerprint):
            flash('Fingerprint does not match!', 'danger')
            return False
        return True

    return current_user.is_authenticated


def get_fingerprint(request):
    return hash(request.headers.get('user-agent'))


@app.route('/')
def index():
    return render_template('index/index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_authenticated(current_user, get_fingerprint(request)):
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if not user or not user.password == password:
            flash('Invalid username or password')
            return redirect(url_for('login'))

        fingerprint = hash(request.headers.get('user-agent'))
        user.fingerprint = fingerprint
        db.session.commit()

        login_user(user, remember=True)
        return redirect(url_for('profile'))

    return render_template('login/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/shop')
def shop():
    if not is_authenticated(current_user, get_fingerprint(request)):
        return redirect(url_for('login'))

    products = db.session.query(Product).all()

    return render_template('shop/shop.html', products=products)


@app.route('/shop/product/<int:product_id>', methods=['GET', 'POST'])
def product(product_id):
    if not is_authenticated(current_user, get_fingerprint(request)):
        return redirect(url_for('login'))

    if request.method == 'POST':
        product_review = ProductReview(
            product_id=product_id,
            user_id=current_user.id,
            comment=request.form['comment'],
            rating=request.form['rating']
        )
        db.session.add(product_review)
        db.session.commit()
        flash('Review added')
    product = db.session.query(Product).filter_by(id=product_id).first()
    product_reviews = db.session.query(ProductReview).filter_by(product_id=product_id).all()

    return render_template('shop/product.html', product=product, product_reviews=product_reviews)


@app.route('/profile')
def profile():
    if not is_authenticated(current_user, get_fingerprint(request)):
        return redirect(url_for('login'))
    return render_template('profile/profile.html', user=current_user)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_first_request
def create_tables():
    for table in db.engine.table_names():
        db.engine.execute(f'DROP TABLE IF EXISTS {table}')

    db.create_all()

    db.session.add(User(username='Eve', password='evil'))
    db.session.add(User(username='Alice', password='good', billing_address='Mekelweg 4', shipping_address='Mekelweg 4', credit_card='4242 4242 4242', credit_card_expiration='06/22', credit_card_cvv='123'))
    db.session.commit()

    user_adam = User.query.filter_by(username='Alice').first()
    db.session.add(Product(name='Bike', price=100, description='A bike', image='/static/img/bike.jpg'))
    db.session.commit()

    product_bike = Product.query.filter_by(name='Bike').first()

    db.session.add(ProductReview(rating=5, comment='A great bike', product_id=product_bike.id, user_id=user_adam.id))
    db.session.commit()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    fingerprint = db.Column(db.String(80))

    billing_address = db.Column(db.String(80))
    shipping_address = db.Column(db.String(80))
    credit_card = db.Column(db.String(80))
    credit_card_expiration = db.Column(db.String(80))
    credit_card_cvv = db.Column(db.String(80))

    def __repr__(self):
        return f'<User {self.id}: {self.username}>'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(80), nullable=False)
    image = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f'<Product {self.id}: {self.name}>'


class ProductReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return f'<ProductReview {self.id}: {self.comment}>'


if __name__ == '__main__':
    app.run(debug=True, host='', port=5000)