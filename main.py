from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "ecommerce_secret_key"


db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ka@960491",
    database="ecommerce_store"
)

cursor = db.cursor(dictionary=True)


@app.route('/')
def home():

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()

    return render_template('home.html', products=products)


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        sql = "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)"
        values = (name, email, password)

        cursor.execute(sql, values)
        db.commit()

        flash("Registration Successful")
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        sql = "SELECT * FROM users WHERE email=%s AND password=%s"
        values = (email, password)

        cursor.execute(sql, values)
        user = cursor.fetchone()

        if user:

            session['user_id'] = user['id']
            session['user_name'] = user['name']

            flash("Login Successful")
            return redirect('/')

        else:
            flash("Invalid Email or Password")

    return render_template('login.html')


@app.route('/logout')
def logout():

    session.clear()

    flash("Logged Out")
    return redirect('/')


@app.route('/product/<int:id>')
def product_details(id):

    sql = "SELECT * FROM products WHERE id=%s"
    values = (id,)

    cursor.execute(sql, values)
    product = cursor.fetchone()

    return render_template('product_details.html', product=product)


@app.route('/add_to_cart/<int:id>')
def add_to_cart(id):

    if 'cart' not in session:
        session['cart'] = []

    cart = session['cart']

    cart.append(id)

    session['cart'] = cart

    flash("Product Added To Cart")

    return redirect('/cart')

@app.route('/cart')
def cart():

    cart_items = []
    total = 0

    if 'cart' in session:

        for item_id in session['cart']:

            sql = "SELECT * FROM products WHERE id=%s"
            values = (item_id,)

            cursor.execute(sql, values)
            product = cursor.fetchone()

            if product:
                cart_items.append(product)
                total += float(product['price'])

    return render_template('cart.html',
                           cart_items=cart_items,
                           total=total)


@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):

    if 'cart' in session:

        cart = session['cart']

        if id in cart:
            cart.remove(id)

        session['cart'] = cart

    flash("Item Removed")

    return redirect('/cart')



@app.route('/checkout', methods=['GET', 'POST'])
def checkout():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        user_id = session['user_id']

        total_amount = request.form['total_amount']

        sql = """
        INSERT INTO orders (user_id, total_amount, status)
        VALUES (%s,%s,%s)
        """

        values = (user_id, total_amount, "Placed")

        cursor.execute(sql, values)
        db.commit()

        order_id = cursor.lastrowid

        if 'cart' in session:

            for item_id in session['cart']:

                sql2 = "SELECT * FROM products WHERE id=%s"
                values2 = (item_id,)

                cursor.execute(sql2, values2)
                product = cursor.fetchone()

                if product:

                    insert_item = """
                    INSERT INTO order_items
                    (order_id, product_id, quantity, price)
                    VALUES (%s,%s,%s,%s)
                    """

                    item_values = (
                        order_id,
                        product['id'],
                        1,
                        product['price']
                    )

                    cursor.execute(insert_item, item_values)

            db.commit()

        session['cart'] = []

        flash("Order Placed Successfully")

        return redirect('/orders')

    return render_template('checkout.html')



@app.route('/orders')
def orders():

    if 'user_id' not in session:
        return redirect('/login')

    sql = "SELECT * FROM orders WHERE user_id=%s  ORDER BY CAST(id AS UNSIGNED) ASC"

    values = (session['user_id'],)

    cursor.execute(sql, values)

    orders = cursor.fetchall()

    return render_template('orders.html', orders=orders)



@app.route('/admin')
def admin_dashboard():

    cursor.execute("SELECT COUNT(*) as total_products FROM products")
    products = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    users = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as total_orders FROM orders")
    orders = cursor.fetchone()

    return render_template(
        'admin_dashboard.html',
        products=products,
        users=users,
        orders=orders
    )


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():

    if request.method == 'POST':

        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image = request.form['image']

        sql = """
        INSERT INTO products
        (name, description, price, image)
        VALUES (%s,%s,%s,%s)
        """

        values = (name, description, price, image)

        cursor.execute(sql, values)
        db.commit()

        flash("Product Added Successfully")

        return redirect('/admin')

    return render_template('add_product.html')


@app.route('/delete_product/<int:id>')
def delete_product(id):

    sql = "DELETE FROM products WHERE id=%s"
    values = (id,)

    cursor.execute(sql, values)
    db.commit()

    flash("Product Deleted")

    return redirect('/admin')


if __name__ == '__main__':
    app.run(debug=True)