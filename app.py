from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
import json
import pytz



app = Flask(__name__)
app.secret_key = 'your_secret_key'

# app.jinja_env.filters['tojson'] = json.dumps

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['TIMEZONE'] = 'Africa/Nairobi'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='staff')

class StockItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(50))
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    sales = db.relationship('SaleItem', back_populates='stock_item')  # Added relationship

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float)
    payment_method = db.Column(db.String(20))
    mpesa_code = db.Column(db.String(50))
    items = db.relationship('SaleItem', back_populates='sale')  # Added back_populates

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('stock_item.id'))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    sale = db.relationship('Sale', back_populates='items')  # Added relationship
    stock_item = db.relationship('StockItem', back_populates='sales')

# Create tables
with app.app_context():
    db.create_all()

# Routes
# @app.route('/')
# def home():
#     if 'user_id' in session:
#         if session['role'] == 'admin':
#             return redirect(url_for('admin_dashboard'))
#         return redirect(url_for('pos'))
#     return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user_id' in session:
        # Redirect everyone to POS interface regardless of role
        return redirect(url_for('pos'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('home'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.before_request
def set_timezone():
    # Set to Africa/Nairobi or your local timezone
    g.timezone = pytz.timezone('Africa/Nairobi')

# Add a template filter
@app.template_filter('local_time')
def local_time_filter(dt):
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(g.timezone).strftime('%Y-%m-%d %H:%M')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        old_pass = request.form['old_password']
        new_pass = request.form['new_password']
        confirm_pass = request.form['confirm_password']
        
        # Validate new password
        if new_pass != confirm_pass:
            flash('New passwords do not match!')
            return redirect(url_for('change_password'))
        
        if len(new_pass) < 8:
            flash('Password must be at least 8 characters long!')
            return redirect(url_for('change_password'))
        
        # Verify old password
        if check_password_hash(user.password, old_pass):
            user.password = generate_password_hash(new_pass)
            db.session.commit()
            flash('Password changed successfully!')
            return redirect(url_for('home'))
        else:
            flash('Incorrect current password')
    
    return render_template('change_password.html')

# Admin Routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    return render_template('admin/dashboard.html')

@app.route('/admin/stock')
def stock_list():
    items = StockItem.query.all()
    return render_template('admin/stock_list.html', items=items)

@app.route('/admin/stock/add', methods=['GET', 'POST'])
def add_stock():
    if request.method == 'POST':
        new_item = StockItem(
            name=request.form['name'],
            buying_price=float(request.form['buying_price']),
            selling_price=float(request.form['selling_price']),
            size=request.form.get('size'),
            quantity=int(request.form['quantity']),
            description=request.form.get('description')
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item added successfully!')
        return redirect(url_for('stock_list'))
    return render_template('admin/add_stock.html')

@app.route('/admin/stock/edit/<int:id>', methods=['GET', 'POST'])
def edit_stock(id):
    item = StockItem.query.get(id)
    if request.method == 'POST':
        item.name = request.form['name']
        item.buying_price = float(request.form['buying_price'])
        item.selling_price = float(request.form['selling_price'])
        item.size = request.form.get('size')
        item.quantity = int(request.form['quantity'])
        item.description = request.form.get('description')
        db.session.commit()
        flash('Item updated successfully!')
        return redirect(url_for('stock_list'))
    return render_template('admin/edit_stock.html', item=item)

@app.route('/admin/stock/delete/<int:id>')
def delete_stock(id):
    item = StockItem.query.get(id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully!')
    return redirect(url_for('stock_list'))

# @app.route('/admin/profit-analysis')
# def profit_analysis():
#     # Calculate daily profits
#     sales = Sale.query.all()
#     profit_data = {}
#     sorted_dates = sorted(profit_data.keys())
    
#     for sale in sales:
#         date_str = sale.date.strftime('%Y-%m-%d')
#         if date_str not in profit_data:
#             profit_data[date_str] = {'sales': 0, 'profit': 0}
        
#         for item in sale.items:
#             stock_item = StockItem.query.get(item.item_id)
#             if stock_item:  # Ensure stock item exists
#                 profit = (item.price - stock_item.buying_price) * item.quantity
#                 profit_data[date_str]['profit'] += profit
#             profit_data[date_str]['sales'] += item.price * item.quantity
    
#     # Prepare data for chart
#     chart_data = {
#         'dates': sorted_dates,
#         'sales': [data['sales'] for data in profit_data.values()],
#         'profits': [data['profit'] for data in profit_data.values()]
#     }
    
#     return render_template('admin/profit_analysis.html', 
#                            profit_data=profit_data,
#                            chart_data=chart_data)
@app.route('/admin/profit-analysis')
def profit_analysis():
    # Calculate daily profits
    sales = Sale.query.all()
    profit_data = {}
    
    for sale in sales:
        date_str = sale.date.strftime('%Y-%m-%d')
        if date_str not in profit_data:
            profit_data[date_str] = {'sales': 0, 'profit': 0}
        
        for item in sale.items:
            if item.stock_item:  # Check if stock item exists
                profit = (item.price - item.stock_item.buying_price) * item.quantity
                profit_data[date_str]['profit'] += profit
            profit_data[date_str]['sales'] += item.price * item.quantity
    
    # Prepare data for chart
    chart_data = {
        'dates': list(profit_data.keys()),
        'sales': [data['sales'] for data in profit_data.values()],
        'profits': [data['profit'] for data in profit_data.values()]
    }
    
    return render_template('admin/profit_analysis.html', 
                           profit_data=profit_data,
                           chart_data=chart_data)

# POS Routes
@app.route('/pos')
def pos():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    items = StockItem.query.filter(StockItem.quantity > 0).all()
    return render_template('sales/pos.html', items=items)

@app.route('/sales-viewer')
def sales_viewer():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    sales = Sale.query.all()
    return render_template('admin/sales_viewer.html', sales=sales)

@app.route('/receipt/<int:sale_id>')
def receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('receipt.html', sale=sale)

@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        # Parse cart data
        cart = json.loads(request.form['cart'])
        payment_method = request.form['payment_method']
        mpesa_code = request.form.get('mpesa_code', '')
        total = float(request.form['total'])
        
        # Create sale record
        new_sale = Sale(
            total_amount=total,
            payment_method=payment_method,
            mpesa_code=mpesa_code
        )
        db.session.add(new_sale)
        db.session.flush()  # Get sale ID before commit
        
        # Create sale items and update stock
        for item in cart:
            stock_item = StockItem.query.get(item['id'])
            if not stock_item:
                flash(f"Item ID {item['id']} not found!", 'error')
                return redirect(url_for('pos'))
                
            if stock_item.quantity < item['quantity']:
                flash(f"Not enough stock for {stock_item.name}!", 'error')
                return redirect(url_for('pos'))
                
            sale_item = SaleItem(
                sale_id=new_sale.id,
                item_id=item['id'],
                quantity=item['quantity'],
                price=item['price']
            )
            stock_item.quantity -= item['quantity']
            db.session.add(sale_item)
        
        db.session.commit()
        return render_template('sales/checkout.html', sale=new_sale)
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Checkout error: {str(e)}")
        flash(f"Checkout failed: {str(e)}", 'error')
        return redirect(url_for('pos'))

@app.route('/add-sample-data')
def add_sample_data():
    with app.app_context():
        # Add sample stock items
        item1 = StockItem(
            name="T-Shirt",
            buying_price=5.99,
            selling_price=12.99,
            size="M",
            quantity=100,
            description="Cotton t-shirt"
        )
        
        item2 = StockItem(
            name="Jeans",
            buying_price=15.50,
            selling_price=29.99,
            size="32",
            quantity=50,
            description="Blue denim jeans"
        )
        
        db.session.add(item1)
        db.session.add(item2)
        db.session.commit()
    
    return "Sample data added!"

@app.route('/health')
def health_check():
    return 'OK', 200

@app.route('/create_admin')
def initialize_database():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create admin user if it doesn't exist
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
    initialize_database()
    app.run(debug=True)