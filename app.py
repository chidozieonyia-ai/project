from flask import Flask, request, redirect, render_template, redirect, flash
import json
import os

app = Flask(__name__)
app.secret_key = "mysecretkey"

FILE_NAME = "stock.txt"

def load_products():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as file:
            return json.load(file)
    return {}

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

                if product in products:
                    products[product]["quantity"] += quantity
                else:
                    products[product] = {"quantity": quantity, "min": 2}

                flash(f"{product} added successfully!", "success")

            elif action == "reduce":
                quantity = int(quantity)

                if product in products:
                    if products[product]["quantity"] >= quantity:
                        products[product]["quantity"] -= quantity
                        flash(f"{quantity} removed from {product}!")
                    else:
                        flash("Not enough stock!", "error")

            elif action == "set_min":
                quantity = int(quantity)

                if product in products:
                    products[product]["min"] = quantity
                    flash(f"Minimum updated for {product}!", "success")           

            elif action == "delete":
                if product in products:
                    del products[product]
                    flash(f"{product} deleted!", "success")

        save_products(products)
        return redirect("/")

    return render_template("index.html", products=products)

if __name__ == "__main__":
    app.run(debug=True)