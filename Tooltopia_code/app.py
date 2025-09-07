from flask import Flask, request, render_template, jsonify, flash, redirect, url_for,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user,login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
import os
from decimal import Decimal, ROUND_HALF_UP

class AdminLoginForm(FlaskForm):
    admin_password = PasswordField('Admin Password', validators=[DataRequired()])
    submit = SubmitField('Enter Admin Area')


# Initialize the Flask App
app = Flask(__name__)
def money(value) -> Decimal:
    
    d = Decimal(str(value))
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

@app.template_filter('currency')
def currency(value):
    try:
        d = Decimal(str(value))
    except Exception:
        return "£0.00"
    d = d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"£{d:,.2f}"


# Configure the App
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Necessary for session management and form protection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the Database
db = SQLAlchemy(app)

# Define the User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)  


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Define the Product Model

    def __repr__(self):
        return f'<Product {self.name}>'

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Define Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(150), nullable=True)
    description = db.Column(db.Text, nullable=True)
    stock = db.Column(db.Integer, default=0)  # Assumes a default stock level of 0 for new products


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)

    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))


    def __repr__(self):
        return f'<Product {self.name}>'

cart_items = []  

def create_tables():
    db.create_all()
    if not Product.query.first():
        db.session.add(Product(name="Star screwdriver", price=2.99, image="product1.jpg", description="Star screwdriver DB,this screwdriver is made from steel and has a magnetic end to make picking up screwdrivers easy!", stock=100))
        db.session.add(Product(name="3/4 ratchet", price=15.34, image="product3.jpg", description="Xtool 3/4 ratchet with 120 degrees rotation, anticlockwise rotation, and clockwise", stock=64))
        db.session.add(Product(name="Flathead screwdriver", price=2.99, image="product2.jpeg", description="Steudt Flathead screwdriver 100% steel with magnetic tip", stock=24))
        db.session.add(Product(name="1/2 ratchet", price=20.34, image="product4.jpg", description="Xtool 1/2 ratchet with 150 degrees rotation, no included sockets bit", stock=59))
        db.session.add(Product(name="Air compressed spray 500ml", price=15.34, image="product5.jpg", description="liquimoley compressed air spray 500ml, invertable and easy to use", stock=23))
        db.session.add(Product(name="Denso k20hr-u11", price=59.99, image="product6.jpeg", description="Denso spark plug copper tip for great combustion performance", stock=4))
        db.session.add(Product(name="ignition coil denso type2", price=49.99, image="product7.jpg", description="Denso ignition coil for Toyota Aygo, Citroen C1 type 2 ignition coil", stock=15))
        db.session.add(Product(name="Denso 1KW starter", price=149.99, image="product8.jpeg",description="starter for smaller car,specifically for toyota aygo rated power:1KW",stock=3))
 
        db.session.commit()

with app.app_context():
    create_tables()
# Route Definitions
@app.route('/')
def home_page():
    products = Product.query.all()
    return render_template('main.html', products=products)

@app.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    product = Product.query.get(product_id)

    if product and product.stock > 0:
        existing_item = CartItem.query.filter_by(
            user_id=current_user.id, product_id=product_id
        ).first()
        if existing_item:
            if existing_item.quantity < product.stock:
                existing_item.quantity += 1
            else:
                return jsonify({"ok": False, "message": "Not enough stock."}), 400
        else:
            db.session.add(CartItem(user_id=current_user.id, product_id=product_id))
        db.session.commit()
        return jsonify({"ok": True, "message": f'"{product.name}" added to cart.'}), 200

    return jsonify({"ok": False, "message": "Product not found or out of stock."}), 404



@app.route('/cart')
@login_required
def cart():
    # Fetches items
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()

    # Computes per-line totals using Decimal for accuracy
    line_totals = {}
    for ci in cart_items:
        unit = Decimal(str(ci.product.price))          
        qty  = Decimal(str(ci.quantity))
        line_totals[ci.id] = money(unit * qty)        

    # Grand total
    total_price = money(sum(line_totals.values(), Decimal("0")))

    return render_template(
        "results.html",
        cart_items=cart_items,
        line_totals=line_totals,   
        total_price=total_price,   
    )


@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get(item_id)
    if item and item.user_id == current_user.id:  # Ensures the item exists and belongs to the current user
        db.session.delete(item)
        db.session.commit()
        flash('Item removed from cart.')
    else:
        flash('Item could not be found.')
    return redirect(url_for('cart'))


@app.route('/update_quantity/<int:item_id>', methods=['POST'])
@login_required
def update_quantity(item_id):
    item = CartItem.query.get(item_id)
    if item and item.user_id == current_user.id:  # Ensures the item exists and belongs to the current user
        try:
            new_quantity = int(request.form.get('quantity'))
            if new_quantity > 0:
                item.quantity = new_quantity
                db.session.commit()
                flash('Quantity updated.')
            else:
                flash('Invalid quantity.')
        except ValueError:
            flash('Invalid input for quantity.')
    else:
        flash('Item not found.')
    return redirect(url_for('cart'))


@app.route("/results.html")
def nextpage():
    # This creates a dictionary where each key is a product ID
    products = {str(product.id): product for product in Product.query.all()}
    return render_template('results.html', cart_items=cart_items, products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user is not None:
            flash('Username already taken. Please choose a different one.')
            return redirect(url_for('register'))

        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        # Redirects to the home page
        return redirect(url_for('home_page'))  
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home_page'))

@app.route('/search')
def search():
    query = request.args.get('q')
    if query:
        products = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
        results = [{'id': p.id, 'name': p.name} for p in products]
        return jsonify(results)
    return jsonify([])
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not items:
        flash("Your cart is empty.", "info")
        return redirect(url_for('cart'))

    # Computes total with Decimal and check stock
    out_of_stock = []
    total = Decimal("0.00")
    for ci in items:
        product = ci.product  
        if product.stock < ci.quantity:
            out_of_stock.append(product.name)
        # keeps both operands Decimal
        total += Decimal(str(product.price)) * Decimal(str(ci.quantity))

    if out_of_stock:
        flash(f"Not enough stock for {', '.join(out_of_stock)}.", "error")
        return redirect(url_for('cart'))

    # Deducts stock and clear cart
    for ci in items:
        ci.product.stock -= ci.quantity
        db.session.delete(ci)

    db.session.commit()

    total = money(total)  # rounds to 2 dp with the helper
    flash(f"Thank you for your purchase! Total amount: £{total}", "success")
    return redirect(url_for('home_page'))



@app.route('/admin-login', methods=['GET', 'POST'])
@login_required
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        if form.admin_password.data == '112911':
            session['admin_access'] = True
            return redirect(url_for('admin'))
        else:
            flash('Incorrect admin password.')
            session.pop('admin_access', None)
   
    return render_template('admin_login.html', form=form)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    print("Admin access session variable:", session.get('admin_access'))  # For debugging
    if 'admin_access' not in session:
        return redirect(url_for('admin_login'))

    products = Product.query.all()
    return render_template('admin.html', products=products)

    
    products = Product.query.all()
    return render_template('admin.html', products=products)

@app.route('/update_stock/<int:product_id>', methods=['POST'])
@login_required
def update_stock(product_id):
    # Checks if the 'admin_access' session variable is set, implying they've passed the admin login.
    if not session.get('admin_access'):
        flash('You do not have access to this page.')
        return redirect(url_for('admin_login'))

    product = Product.query.get_or_404(product_id)
    try:
        new_stock = int(request.form['stock'])
        product.stock = new_stock
        db.session.commit()
        flash('Stock updated successfully!')
    except ValueError:
        flash('Invalid input for stock.')

    return redirect(url_for('admin'))

@app.route('/admin-logout')
@login_required
def admin_logout():
    session.pop('admin_access', None)
    flash('You have been logged out of the admin area.')
    return redirect(url_for('home_page'))

@app.route('/search-products')
@login_required
def search_products():
    query = request.args.get('q', '')
    if query:
        products = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
        return jsonify([{'id': p.id, 'name': p.name} for p in products])
    return jsonify([])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create all tables initially if they don't exist.
    app.run(debug=True)
