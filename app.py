from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = 'test1'  # Замените  на ваш секретный ключ

DATABASE = 'database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = [dict((cur.description[idx][0], value) for idx, value in enumerate(row)) for row in cur.fetchall()]
    cur.close()
    return (rv[0] if rv else None) if one else rv

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    username = session.get('username', 'Гость')
    return render_template('index.html', username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = query_db('SELECT * FROM users WHERE username = ? AND password = ?', [username, password], one=True)
        
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return 'Неправильное имя пользователя или пароль'

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role=None
        if password=='adm':
            role='admin'
        else:
            role='user'
        query_db('INSERT INTO users (username, password) VALUES (?, ?)', [username, password])
        get_db().commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/products')
def products():
    products = query_db('SELECT * FROM products')
    return render_template('products.html', products=products)

@app.route('/my_orders')
def my_orders():
    if 'username' not in session:
        return redirect(url_for('login'))
    orders = query_db('''
        SELECT orders.id, products.name, orders.quantity, products.price
        FROM orders
        JOIN users ON orders.user_id = users.id
        JOIN products ON orders.product_id = products.id
    ''')
    
    return render_template('my_orders.html', orders=orders)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_name = request.form['name']
        product_price = request.form['price']
        product_description = request.form['description']
        product_image_url = request.form['image_url']  
        query_db('INSERT INTO products (name, price, description, image_url) VALUES (?, ?, ?, ?)',
                 [product_name, product_price, product_description, product_image_url])
        get_db().commit()

        return redirect(url_for('products'))

    return render_template('add_product.html')
@app.route('/manage_orders')
def manage_orders():
    orders = query_db('''
        SELECT orders.id, users.username, products.name, orders.quantity, products.price
        FROM orders
        JOIN users ON orders.user_id = users.id
        JOIN products ON orders.product_id = products.id
    ''')
    return render_template('manage_orders.html', orders=orders)

@app.route('/order/<int:product_id>', methods=['POST'])
def order(product_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    quantity = int(request.form['quantity'])
    user_id = query_db('SELECT id FROM users WHERE username = ?', [session['username']], one=True)['id']

    query_db('INSERT INTO orders (user_id, product_id, quantity) VALUES (?, ?, ?)',
             [user_id, product_id, quantity])
    get_db().commit()

    return redirect(url_for('my_orders'))

@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    query_db('DELETE FROM orders WHERE id = ?', [order_id])
    get_db().commit()

    return redirect(url_for('manage_orders'))

if __name__ == '__main__':
    app.run(debug=True)