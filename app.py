from flask import Flask, request, redirect, render_template, redirect, flash
import sqlite3
import json
import os

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("stock.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        minimum_level INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()

init_db()
app.secret_key = "mysecretkey"

FILE_NAME = "stock.txt"

def load_products():
    conn = sqlite3.connect("stock.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT product, quantity, minimum_level FROM products"
    )

    rows = cursor.fetchall()

    conn.close()

    products = {}

    for row in rows:
        product_name = row[0]

        products[product_name] = {
            "quantity": row[1],
            "min": row[2]
        }

    return products

def save_products(products):
    with open(FILE_NAME, "w") as file:
        json.dump(products, file)

@app.route("/", methods=["GET", "POST"])
def home():
    products = load_products()

    product = None
    quantity = None
    action = None

    if request.method == "POST":
        action = request.form.get("action")
        product = request.form.get("product")
        quantity = request.form.get("quantity")

        if product:

            if action == "add":
                quantity = int(quantity)

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
                        "UPDATE products SET quantity = ? WHERE product = ?",
                        (new_quantity, product)
                    )

                else:
                    cursor.execute(
                        "INSERT INTO products (product, quantity, minimum_level) VALUES (?, ?, ?)",
                        (product, quantity, 2)
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

                        flash(f"{quantity} removed from {product}!")
                    else:
                        flash("Not enough stock!", "error")

                conn.close()

            elif action == "set_min":
                quantity = int(quantity)

                if product in products:
                    products[product]["min"] = quantity
                    flash(f"Minimum updated for {product}!", "success")           

            elif action == "delete":

                conn = sqlite3.connect("stock.db")
                cursor = conn.cursor()

                cursor.execute(
                    "DELETE FROM products WHERE product=?",
                    (product,)
                )

                conn.commit()
                conn.close()

                flash(f"{product} deleted!", "success")

        save_products(products)
        return redirect("/")

    return render_template("index.html", products=products)

if __name__ == "__main__":
    app.run(debug=True)