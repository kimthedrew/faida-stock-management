from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
from datetime import datetime, timedelta
import calendar
import json
import pytz



app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.jinja_env.filters['tojson'] = json.dumps

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
    created_by = db.Column(db.String(80))
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


@app.template_filter('format_currency')
def format_currency_filter(value):
    return "{:,.2f}".format(value)

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
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        # Search across name, size, and description fields
        items = StockItem.query.filter(
            db.or_(
                StockItem.name.contains(search_query),
                StockItem.size.contains(search_query),
                StockItem.description.contains(search_query)
            )
        ).all()
    else:
        items = StockItem.query.all()
    
    return render_template('admin/stock_list.html', items=items, search_query=search_query)

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
# @app.route('/admin/profit-analysis')
# def profit_analysis():
#     # Calculate daily profits
#     sales = Sale.query.all()
#     profit_data = {}
    
#     for sale in sales:
#         date_str = sale.date.strftime('%Y-%m-%d')
#         if date_str not in profit_data:
#             profit_data[date_str] = {'sales': 0, 'profit': 0}
        
#         for item in sale.items:
#             if item.stock_item:  # Check if stock item exists
#                 profit = (item.price - item.stock_item.buying_price) * item.quantity
#                 profit_data[date_str]['profit'] += profit
#             profit_data[date_str]['sales'] += item.price * item.quantity
    
#     # Prepare data for chart
#     chart_data = {
#         'dates': list(profit_data.keys()),
#         'sales': [data['sales'] for data in profit_data.values()],
#         'profits': [data['profit'] for data in profit_data.values()]
#     }
    
#     return render_template('admin/profit_analysis.html', 
#                            profit_data=profit_data,
#                            chart_data=chart_data)

# app.py (profit_analysis route)

@app.route('/admin/profit-analysis')
def profit_analysis():
    """
    Robust profit analysis route:
    - Accepts time_range values sent by the template: 'today', 'week', 'month', 'quarter', 'year'
    - Converts date range to naive UTC datetimes for DB querying (assumes DB datetimes are naive UTC)
    - Localizes sale datetimes correctly and groups by Nairobi date
    - Zero-fills missing dates so chart arrays are same length and chronological
    - Builds chart_data with 'dates', 'sales', 'profits', 'expenses'
    """
    # Get time range from query parameter (template uses values like 'today','week','month','quarter','year')
    time_range = request.args.get('time_range', 'week')

    nairobi_tz = pytz.timezone(app.config.get('TIMEZONE', 'Africa/Nairobi'))
    today = datetime.now(nairobi_tz).date()

    # Determine start_date based on requested range
    if time_range in ('today', 'day'):
        start_date = today
    elif time_range == 'week':
        start_date = today - timedelta(days=6)
    elif time_range == 'month':
        start_date = today.replace(day=1)
    elif time_range == 'quarter':
        # approximate quarter = last 90 days (you can adjust to exact quarter start if needed)
        start_date = today - timedelta(days=90)
    elif time_range == 'year':
        start_date = today.replace(month=1, day=1)
    else:
        # fallback to last 30 days
        start_date = today - timedelta(days=29)

    end_date = today

    # Build aware datetimes in Nairobi, then convert to UTC and then to naive UTC datetimes for DB comparison
    start_dt_nairobi = nairobi_tz.localize(datetime.combine(start_date, datetime.min.time()))
    end_dt_nairobi   = nairobi_tz.localize(datetime.combine(end_date,   datetime.max.time()))

    # Convert to UTC (aware), then to naive by removing tzinfo (common pattern if DB stores naive UTC)
    utc_start_aware = start_dt_nairobi.astimezone(pytz.UTC)
    utc_end_aware   = end_dt_nairobi.astimezone(pytz.UTC)
    utc_start_naive = utc_start_aware.replace(tzinfo=None)
    utc_end_naive   = utc_end_aware.replace(tzinfo=None)

    # Query sales between these naive UTC datetimes
    sales = Sale.query.filter(Sale.date >= utc_start_naive).filter(Sale.date <= utc_end_naive).all()

    # Prepare containers
    profit_data = {}            # keyed by ISO date 'YYYY-MM-DD'
    # We'll track cost (buying_price * qty) so expenses = cost
    # and revenue (price * qty)
    all_items_sold = []         # list of dicts per sold item for further aggregations

    # Aggregate per sale
    for sale in sales:
        # Ensure sale.date is treated as UTC-aware before converting to Nairobi
        sale_dt = sale.date
        if sale_dt is None:
            continue

        if sale_dt.tzinfo is None:
            # DB-stored naive -> we assume it's UTC
            sale_dt_aware = pytz.UTC.localize(sale_dt)
        else:
            sale_dt_aware = sale_dt

        sale_date_nairobi = sale_dt_aware.astimezone(nairobi_tz).date()
        date_key = sale_date_nairobi.strftime('%Y-%m-%d')

        if date_key not in profit_data:
            profit_data[date_key] = {'sales': 0.0, 'cost': 0.0, 'profit': 0.0}

        # If you store Sale.total_amount, use it to add to sales. If not, derive from items.
        if sale.total_amount is not None:
            profit_data[date_key]['sales'] += float(sale.total_amount or 0.0)
        # Now iterate items to compute cost and profit accurately
        for item in sale.items:
            # item.price is unit selling price, item.quantity number sold
            qty = float(item.quantity or 0)
            unit_price = float(item.price or 0.0)
            revenue = unit_price * qty

            # Default buying price zero if stock_item missing
            stock_item = None
            if hasattr(item, 'stock_item') and item.stock_item:
                stock_item = item.stock_item
            else:
                stock_item = db.session.get(StockItem, item.item_id)

            buying_price = float(stock_item.buying_price) if stock_item and stock_item.buying_price is not None else 0.0
            cost = buying_price * qty
            profit = revenue - cost

            # Add to per-day totals
            profit_data[date_key]['sales'] += revenue if sale.total_amount is None else 0.0  # avoid double count if total_amount already used
            profit_data[date_key]['cost'] += cost
            profit_data[date_key]['profit'] += profit

            # Save item for product-level analysis
            all_items_sold.append({
                'name': stock_item.name if stock_item else f"Item#{item.item_id}",
                'quantity': int(qty),
                'sale_date': sale_date_nairobi,
                'revenue': revenue,
                'cost': cost,
                'profit': profit
            })

    # Build full date list from start_date .. end_date inclusive (chronological order)
    dates_list = []
    d = start_date
    while d <= end_date:
        dates_list.append(d.strftime('%Y-%m-%d'))
        if d.strftime('%Y-%m-%d') not in profit_data:
            profit_data[d.strftime('%Y-%m-%d')] = {'sales': 0.0, 'cost': 0.0, 'profit': 0.0}
        d = d + timedelta(days=1)

    # Now ensure chronological order
    dates_list.sort()

    # Build chart arrays (same length, chronological)
    chart_sales = [ round(profit_data[dt]['sales'], 2)   for dt in dates_list ]
    chart_profits = [ round(profit_data[dt]['profit'], 2) for dt in dates_list ]
    chart_expenses = [ round(profit_data[dt]['cost'], 2)  for dt in dates_list ]

    chart_data = {
        'dates': dates_list,
        'sales': chart_sales,
        'profits': chart_profits,
        'expenses': chart_expenses
    }

    # Totals & margins
    total_revenue = sum(chart_sales)
    total_profit = sum(chart_profits)
    profit_margin = (total_profit / total_revenue * 100) if total_revenue else 0.0

    # Build per-product stats
    product_stats = {}
    for it in all_items_sold:
        name = it['name']
        product = product_stats.setdefault(name, {'quantity_sold': 0, 'revenue': 0.0, 'profit': 0.0})
        product['quantity_sold'] += it['quantity']
        product['revenue']      += it['revenue']
        product['profit']       += it['profit']

    top_products_list = []
    for name, stats in product_stats.items():
        margin = (stats['profit'] / stats['revenue'] * 100) if stats['revenue'] else 0.0
        top_products_list.append({
            'name': name,
            'quantity_sold': stats['quantity_sold'],
            'revenue': stats['revenue'],
            'profit': stats['profit'],
            'margin': round(margin, 1)
        })
    top_products_list.sort(key=lambda x: x['profit'], reverse=True)
    top_products_list = top_products_list[:10]

     # Ensure top_product always has a numeric 'change' field so template can round() it
    if top_products_list:
        top_product = top_products_list[0]
        # add default 'change' if missing (use 0.0 or compute a real change)
        if 'change' not in top_product or top_product.get('change') is None:
            top_product['change'] = 0.0
    else:
        top_product = {
            'name': 'N/A',
            'quantity_sold': 0,
            'profit': 0.0,
            'change': 0.0
        }
    # Build daily_item_counts and most_sold_per_day
    daily_item_counts = {}
    for it in all_items_sold:
        date_str = it['sale_date'].strftime('%Y-%m-%d')
        daily_item_counts.setdefault(date_str, {})
        daily_item_counts[date_str][it['name']] = daily_item_counts[date_str].get(it['name'], 0) + it['quantity']

    most_sold_per_day = {}
    for date_key, counts in daily_item_counts.items():
        if counts:
            most_sold_per_day[date_key] = max(counts.items(), key=lambda x: x[1])[0]

    # Weekly and monthly: top product by quantity
    weekly_counts_by_product = {}
    monthly_counts_by_product = {}
    for it in all_items_sold:
        week_key = f"{it['sale_date'].isocalendar()[0]}-W{it['sale_date'].isocalendar()[1]}"
        month_key = it['sale_date'].strftime('%Y-%m')
        weekly_counts_by_product.setdefault((week_key, it['name']), 0)
        weekly_counts_by_product[(week_key, it['name'])] += it['quantity']
        monthly_counts_by_product.setdefault((month_key, it['name']), 0)
        monthly_counts_by_product[(month_key, it['name'])] += it['quantity']

    # find top weekly product overall (across the range)
    weekly_agg = {}
    for (wk, name), qty in weekly_counts_by_product.items():
        weekly_agg[name] = weekly_agg.get(name, 0) + qty
    monthly_agg = {}
    for (mk, name), qty in monthly_counts_by_product.items():
        monthly_agg[name] = monthly_agg.get(name, 0) + qty

    weekly_top_name, weekly_top_qty = ("N/A", 0)
    if weekly_agg:
        weekly_top_name, weekly_top_qty = max(weekly_agg.items(), key=lambda x: x[1])

    monthly_top_name, monthly_top_qty = ("N/A", 0)
    if monthly_agg:
        monthly_top_name, monthly_top_qty = max(monthly_agg.items(), key=lambda x: x[1])

    # Dummy change numbers (replace with actual comparators if you track previous periods)
    revenue_change = 0.0
    profit_change = 0.0
    margin_change = 0.0

    # Get today's items for the template
    today_items = []
    today_date_str = today.strftime('%Y-%m-%d')
    if today_date_str in profit_data:
        # Get today's items from all_items_sold
        today_items = [item for item in all_items_sold if item['sale_date'].strftime('%Y-%m-%d') == today_date_str]
        
        # Group by product name and aggregate
        today_items_grouped = {}
        for item in today_items:
            name = item['name']
            if name not in today_items_grouped:
                today_items_grouped[name] = {
                    'name': name,
                    'quantity': 0,
                    'revenue': 0.0,
                    'profit': 0.0,
                    'unit_price': 0.0
                }
            today_items_grouped[name]['quantity'] += item['quantity']
            today_items_grouped[name]['revenue'] += item['revenue']
            today_items_grouped[name]['profit'] += item['profit']
        
        # Calculate unit price (average)
        for item in today_items_grouped.values():
            if item['quantity'] > 0:
                item['unit_price'] = item['revenue'] / item['quantity']
        
        today_items = list(today_items_grouped.values())

    return render_template('admin/profit_analysis.html',
                           profit_data=profit_data,
                           chart_data=chart_data,
                           total_revenue=total_revenue,
                           total_profit=total_profit,
                           profit_margin=round(profit_margin, 1),
                           revenue_change=revenue_change,
                           profit_change=profit_change,
                           margin_change=margin_change,
                           top_products=top_products_list,
                           top_product=top_product,
                           most_sold_per_day=most_sold_per_day,
                           daily_item_counts=daily_item_counts,
                           weekly_most_sold_name=weekly_top_name,
                           weekly_most_sold_qty=weekly_top_qty,
                           monthly_most_sold_name=monthly_top_name,
                           monthly_most_sold_qty=monthly_top_qty,
                           time_range=time_range,
                           todays_items=today_items,
                           today_date=today.strftime('%B %d, %Y'))



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
    return render_template('sales/receipt.html', sale=sale)

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
            mpesa_code=mpesa_code,
            created_by=session.get('username')
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
    
@app.route('/sales')
def sales():
    # Visible to logged-in users (admin and staff)
    if 'user_id' not in session:
        return redirect(url_for('login'))

    nairobi_tz = pytz.timezone(app.config.get('TIMEZONE', 'Africa/Nairobi'))
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    payment_method = request.args.get('payment_method')
    seller = request.args.get('seller')
    min_amount = request.args.get('min_amount')
    max_amount = request.args.get('max_amount')
    
    # Build query with filters
    sales_q = Sale.query
    
    # Date filters
    if start_date:
        try:
            start_dt = nairobi_tz.localize(datetime.strptime(start_date, '%Y-%m-%d'))
            start_dt_utc = start_dt.astimezone(pytz.UTC).replace(tzinfo=None)
            sales_q = sales_q.filter(Sale.date >= start_dt_utc)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = nairobi_tz.localize(datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))
            end_dt_utc = end_dt.astimezone(pytz.UTC).replace(tzinfo=None)
            sales_q = sales_q.filter(Sale.date < end_dt_utc)
        except ValueError:
            pass
    
    # Payment method filter
    if payment_method and payment_method != 'all':
        sales_q = sales_q.filter(Sale.payment_method == payment_method)
    
    # Seller filter
    if seller and seller != 'all':
        sales_q = sales_q.filter(Sale.created_by == seller)
    
    # Amount filters
    if min_amount:
        try:
            sales_q = sales_q.filter(Sale.total_amount >= float(min_amount))
        except ValueError:
            pass
    
    if max_amount:
        try:
            sales_q = sales_q.filter(Sale.total_amount <= float(max_amount))
        except ValueError:
            pass
    
    # Execute query and order by date desc
    sales_q = sales_q.order_by(Sale.date.desc()).all()

    # Group by date (Nairobi timezone)
    grouped_sales = {}  # { '2025-09-12': [sale1, sale2], ... }
    daily_totals = {}   # { '2025-09-12': 1500.0, ... }

    for sale in sales_q:
        try:
            sale_dt = sale.date
            if sale_dt.tzinfo is None:
                # assume UTC in DB if naive
                sale_dt = pytz.UTC.localize(sale_dt)
            sale_local_date = sale_dt.astimezone(nairobi_tz).date()
        except Exception:
            # fallback: use naive date()
            sale_local_date = sale.date.date()

        date_key = sale_local_date.strftime('%Y-%m-%d')
        if date_key not in grouped_sales:
            grouped_sales[date_key] = []
            daily_totals[date_key] = 0.0

        grouped_sales[date_key].append(sale)
        daily_totals[date_key] += sale.total_amount or 0.0

    # Sort grouped_sales keys descending
    sorted_dates = sorted(grouped_sales.keys(), reverse=True)
    
    # Get unique sellers and payment methods for filter dropdowns
    all_sales = Sale.query.all()
    unique_sellers = list(set([sale.created_by for sale in all_sales if sale.created_by]))
    unique_payment_methods = list(set([sale.payment_method for sale in all_sales if sale.payment_method]))
    
    # Calculate totals for filtered results
    total_sales_count = len(sales_q)
    total_amount = sum(sale.total_amount or 0.0 for sale in sales_q)

    return render_template('sales/sales.html',
                           grouped_sales=grouped_sales,
                           daily_totals=daily_totals,
                           sorted_dates=sorted_dates,
                           unique_sellers=unique_sellers,
                           unique_payment_methods=unique_payment_methods,
                           total_sales_count=total_sales_count,
                           total_amount=total_amount,
                           current_filters={
                               'start_date': start_date,
                               'end_date': end_date,
                               'payment_method': payment_method,
                               'seller': seller,
                               'min_amount': min_amount,
                               'max_amount': max_amount
                           })


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

@app.route('/admin/reset-data', methods=['GET', 'POST'])
def reset_business_data():
    """Reset all sales data to start fresh business operations"""
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # Get confirmation and backup option
            confirm_reset = request.form.get('confirm_reset')
            create_backup = request.form.get('create_backup', False)
            
            if confirm_reset == 'yes':
                # Create backup if requested
                if create_backup:
                    # Export current data to CSV before deletion
                    sales = Sale.query.all()
                    backup_data = []
                    for sale in sales:
                        for item in sale.items:
                            backup_data.append({
                                'sale_id': sale.id,
                                'date': sale.date.strftime('%Y-%m-%d %H:%M:%S'),
                                'total_amount': sale.total_amount,
                                'payment_method': sale.payment_method,
                                'mpesa_code': sale.mpesa_code,
                                'created_by': sale.created_by,
                                'item_name': item.stock_item.name if item.stock_item else f"Item#{item.item_id}",
                                'quantity': item.quantity,
                                'price': item.price
                            })
                    
                    # Save backup to file
                    import csv
                    from datetime import datetime
                    backup_filename = f"sales_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    with open(backup_filename, 'w', newline='', encoding='utf-8') as csvfile:
                        if backup_data:
                            fieldnames = backup_data[0].keys()
                            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(backup_data)
                    
                    flash(f'Backup created: {backup_filename}', 'info')
                
                # Delete all sales and sale items
                SaleItem.query.delete()
                Sale.query.delete()
                
                # Reset stock quantities to original values (optional)
                reset_stock = request.form.get('reset_stock', False)
                if reset_stock:
                    # You might want to add original_quantity field to StockItem model
                    # For now, we'll just keep current quantities
                    pass
                
                db.session.commit()
                flash('All sales data has been reset successfully! You can now start fresh.', 'success')
                return redirect(url_for('admin_dashboard'))
            else:
                flash('Data reset cancelled.', 'info')
                return redirect(url_for('admin_dashboard'))
                
        except Exception as e:
            db.session.rollback()
            flash(f'Error resetting data: {str(e)}', 'error')
            return redirect(url_for('admin_dashboard'))
    
    # GET request - show confirmation page
    sales_count = Sale.query.count()
    total_sales_amount = db.session.query(db.func.sum(Sale.total_amount)).scalar() or 0
    
    return render_template('admin/reset_data.html', 
                         sales_count=sales_count, 
                         total_sales_amount=total_sales_amount)

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)