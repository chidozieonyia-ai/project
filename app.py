from flask import Flask, request, redirect, render_template, flash, Response, session
import sqlite3
import json
import os
import csv

app = Flask(__name__)
app.secret_key = "chido_secret_key"

def init_db():
   
    conn = sqlite3.connect("stock.db")
   
    cursor = conn.cursor()
   

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        minimum_level INTEGER NOT NULL,
        cost_price REAL DEFAULT 0,
        markup REAL DEFAULT 0,
        selling_price REAL DEFAULT 0,
        currency TEXT DEFAULT '₦'
    )
    """)

    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT,
        product TEXT,
        quantity INTEGER,
        timestamp DATETIME DEFAULT 
    CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            password TEXT
        )
        """
    )

    cursor.execute("SELECT * FROM settings")

    settings = cursor.fetchone()

    if not settings:

        cursor.execute(
            """
            INSERT INTO settings (password)
            VALUES (?)
            """,
            ("1234",)
        )

    conn.commit()
    
    conn.close()

init_db()
def upgrade_db():
    conn = sqlite3.connect("stock.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN cost_price REAL DEFAULT 0"
        )
    except:
        pass

    try:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN markup REAL DEFAULT 0"
        )
    except:
        pass

    try:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN selling_price REAL DEFAULT 0"
        )
    except:
        pass

    try:
        cursor.execute(
            "ALTER TABLE products ADD COLUMN currency TEXT DEFAULT '₦'"
        )
    except:
        pass

    conn.commit()
    conn.close()

upgrade_db()
app.secret_key = "mysecretkey"

FILE_NAME = "stock.txt"

def load_products():
    conn = sqlite3.connect("stock.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT product, quantity, minimum_level,
               cost_price, markup, selling_price, currency
        FROM products
        """
    )

    rows = cursor.fetchall()
    conn.close()

    products = {}

    for row in rows:
        products[row[0]] = {
            "quantity": row[1],
            "min": row[2],
            "cost_price": row[3],
            "markup": row[4],
            "selling_price": row[5],
            "currency": row[6]
        }

    return products

def save_products(products):
    with open(FILE_NAME, "w") as file:
        json.dump(products, file)

@app.route("/login", methods=["GET", "POST"])

def login():

    if request.method == "POST":

        username = request.form["username"]

        password = request.form["password"]

        conn = sqlite3.connect("stock.db")

        cursor = conn.cursor()

        cursor.execute("SELECT password FROM settings WHERE id = 1")

        saved_password = cursor.fetchone()[0]

        conn.close()

        if username == "admin" and password == saved_password:

            session["user"] = username

            flash("Login successful!", "success")

            return redirect("/")

        else:

            flash("Invalid username or password!", "error")

    return render_template("login.html")

@app.route("/logout")

def logout():

    session.pop("user", None)

    flash("Logged out successfully!", "success")

    return redirect("/login")

@app.route("/change_password", methods=["GET", "POST"])

def change_password():

    if "user" not in session:
        return redirect("/login")

    if request.method == "POST":

        old_password = request.form["old_password"]

        new_password = request.form["new_password"]

        confirm_password = request.form["confirm_password"]

        conn = sqlite3.connect("stock.db")

        cursor = conn.cursor()

        cursor.execute(
            "SELECT password FROM settings WHERE id = 1"
        )

        current_password = cursor.fetchone()[0]

        if old_password != current_password:

            flash("Old password is incorrect!", "error")

        elif new_password != confirm_password:

            flash("New passwords do not match!", "error")

        else:

            cursor.execute(
                """
                UPDATE settings
                SET password = ?
                WHERE id = 1
                """,
                (new_password,)
            )

            conn.commit()

            flash("Password changed successfully!", "success")

            conn.close()

            return redirect("/")

    return render_template("change_password.html")    

@app.route("/", methods=["GET", "POST"])
def home():

    if "user" not in session:
        return redirect("/login") 

    products = load_products()

    conn = sqlite3.connect("stock.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT action, product, quantity, timestamp
        FROM history
        ORDER BY id DESC
        LIMIT 10
        """
    )

    history = cursor.fetchall()

    conn.close()

    product = None
    quantity = None
    action = None

    if request.method == "POST":
        action = request.form.get("action")
        product = request.form.get("product")
        quantity = request.form.get("quantity")

        if product:

            if action == "add":

                quantity = int(request.form["quantity"])

                cost_price = float(request.form["cost_price"])

                markup = float(request.form["markup"])

                currency = request.form["currency"]

                selling_price = cost_price + (cost_price * markup / 100)

                conn = sqlite3.connect("stock.db")
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT quantity FROM products WHERE product = ?",
                    (product,)
                )

                existing_product = cursor.fetchone()

                if existing_product:

                    new_quantity = existing_product[0] + quantity

                    cursor.execute(
                        """
                        UPDATE products
                        SET quantity = ?,
                            cost_price = ?,
                            markup = ?,
                            selling_price = ?,
                            currency = ?
                        WHERE product = ?
                        """,
                        (
                            new_quantity,
                            cost_price,
                            markup,
                            selling_price,
                            currency,
                            product
                        )
                    )

                else:

                    cursor.execute(
                        """
                        INSERT INTO products
                        (
                            product,
                            quantity,
                            minimum_level,
                            cost_price,
                            markup,
                            selling_price,
                            currency
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            product,
                            quantity,
                            2,
                            cost_price,
                            markup,
                            selling_price,
                            currency
                        )
                    )

                conn.commit()

                cursor.execute(
                """
                INSERT INTO history (action, product, quantity)
                VALUES (?, ?, ?)
                """,
                    ("Added", product, quantity)
                )

                conn.commit()
                
                conn.close()

                flash(f"{product} added successfully!", "success")

            elif action == "reduce":
                quantity = int(quantity)

                conn = sqlite3.connect("stock.db")
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT quantity FROM products WHERE product=?",
                    (product,)
                )

                row = cursor.fetchone()

                if row:
                    current_quantity = row[0]

                    if current_quantity >= quantity:
                        new_quantity = current_quantity - quantity

                        cursor.execute(
                            "UPDATE products SET quantity=? WHERE product=?",
                            (new_quantity, product)
                        )

                        conn.commit()
       
                        cursor.execute(
                            """
                            INSERT INTO history (action, product, quantity)
                            VALUES (?, ?, ?)
                            """,
                            ("Reduced", product, quantity)
                        )

                        conn.commit()

                        conn.close()

                        flash(f"{quantity} removed from {product}!")
                    else:
                        flash("Not enough stock!", "error")

                conn.close()

            elif action == "set_min":
                quantity = int(quantity)

                conn = sqlite3.connect("stock.db")
                cursor = conn.cursor()

                cursor.execute(
                    "UPDATE products SET minimum_level=? WHERE product=?",
                    (quantity, product)
                )

                conn.commit()
                conn.close()

                flash(f"Minimum updated for {product}!", "success")           

            elif action == "delete":

                conn = sqlite3.connect("stock.db")
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO history (action, product, quantity)
                    VALUES (?, ?, ?)
                    """,
                    ("Deleted", product, 0)
                )

                cursor.execute(
                    "DELETE FROM products WHERE product=?",
                    (product,)
                )

                conn.commit()
                conn.close()

                flash(f"{product} deleted!", "success")

            elif action == "edit":

                quantity = int(request.form["quantity"])

                cost_price = float(request.form["cost_price"])

                markup = float(request.form["markup"])

                minimum_level = int(request.form["minimum_level"])

                currency = request.form["currency"]

                selling_price = cost_price + (cost_price * markup / 100)

                conn = sqlite3.connect("stock.db")

                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE products
                    SET quantity = ?,
                        cost_price = ?,
                        markup = ?,
                        selling_price = ?,
                        minimum_level = ?,
                        currency = ?
                    WHERE product = ?
                    """,
                    (
                        quantity,
                        cost_price,
                        markup,
                        selling_price,
                        minimum_level,
                        currency,
                        product
                    )
                )

                conn.commit()

                cursor.execute(
                    """
                    INSERT INTO history (action, product, quantity)
                    VALUES (?, ?, ?)
                    """,
                    ("Edited", product, quantity)
                )

                conn.commit()

                conn.close()

                flash(f"{product} updated successfully!", "success")   

        save_products(products)
        return redirect("/")

    total_cost_value = 0
    total_selling_value = 0

    for item in products.values():

        total_cost_value += (
            item["quantity"] * item.get("cost_price", 0)
        )

        total_selling_value += (
            item["quantity"] * item.get("selling_price", 0)
        )

    expected_profit = total_selling_value - total_cost_value

    return render_template(
        "index.html",
        products=products,
        history=history,
        total_cost_value=total_cost_value,
        total_selling_value=total_selling_value,
        expected_profit=total_selling_value - total_cost_value,
        total_products=len(products),
        total_quantity=sum(item["quantity"] for item in products.values()),
        low_stock_count=sum(
            1
            for item in products.values()
            if item["quantity"] <= item["min"]
        )
    )

@app.route("/export")

def export_csv():

    conn = sqlite3.connect("stock.db")

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            product,
            quantity,
            cost_price,
            markup,
            selling_price,
            minimum_level,
            currency
        FROM products
        """
    )

    products = cursor.fetchall()

    conn.close()

    output = []

    header = [
        "Product",
        "Quantity",
        "Cost Price",
        "Markup %",
        "Selling Price",
        "Minimum Level",
        "Currency"
    ]

    output.append(",".join(header))

    for row in products:

        output.append(",".join(str(item) for item in row))

    csv_data = "\ufeff" + "\n".join(output)

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={
            "Content-disposition":
            "attachment; filename=inventory.csv"
        }
    )

if __name__ == "__main__":
    app.run(debug=False)