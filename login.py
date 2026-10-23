
from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.secret_key = "my_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mystore.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Product(db.Model):
    __tablename__ = "project"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255))
    category = db.Column(db.String(100))
    description = db.Column(db.Text)
    rating = db.Column(db.Float)


with app.app_context():
    db.create_all()


def login_required():
    return "username" in session


@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template(
                "login.html",
                error="Enter ur name and password"
            )

        existing_user = Users.query.filter_by(name=username).first()

        if existing_user and existing_user.password == password:
            session["username"] = existing_user.name
            return redirect("/products")

        return render_template(
            "login.html",
            error="wrong name or password"
        )

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            return render_template(
                "register.html",
                error="Заполните все поля"
            )

        if Users.query.filter_by(name=username).first():
            return render_template(
                "register.html",
                error="Такой пользователь уже существует"
            )

        new_user = Users(name=username, password=password)

        db.session.add(new_user)
        db.session.commit()

        session["username"] = username

        return redirect("/products")

    return render_template("register.html")


@app.route("/products")
def products():
    if not login_required():
        return redirect("/login")

    search = request.args.get("search", "").strip()

    if search:
        all_products = Product.query.filter(
            db.or_(
                Product.name.ilike(f"%{search}%"),
                Product.category.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        ).all()
    else:
        all_products = Product.query.all()

    return render_template(
        "products.html",
        products=all_products,
        username=session["username"],
        search=search
    )


@app.route("/product/<int:product_id>")
def product_details(product_id):
    if not login_required():
        return redirect("/login")

    product = Product.query.get_or_404(product_id)

    return render_template(
        "product_details.html",
        product=product
    )


@app.route("/add_to_cart/<int:product_id>")
def add_to_cart(product_id):
    if not login_required():
        return redirect("/login")

    Product.query.get_or_404(product_id)

    cart = session.get("cart", {})
    product_id = str(product_id)

    cart[product_id] = cart.get(product_id, 0) + 1
    session["cart"] = cart

    return redirect("/cart")


@app.route("/cart")
def cart():
    if not login_required():
        return redirect("/login")

    cart_items = session.get("cart", {})

    products = []
    total = 0

    for product_id, quantity in cart_items.items():
        product = Product.query.get(int(product_id))

        if product and isinstance(quantity, int) and quantity > 0:
            products.append({
                "product": product,
                "quantity": quantity
            })
            total += product.price * quantity

    return render_template(
        "cart.html",
        products=products,
        total=total
    )


@app.route("/add_products", methods=["GET", "POST"])
def get_products():
    if not login_required():
        return redirect("/login")

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price_text = request.form.get("price", "").strip()
        image = request.form.get("image", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        rating_text = request.form.get("rating", "").strip()

        if not name or not price_text:
            return render_template(
                "add_products.html",
                error=""
            )


        try:
            price = float(price_text)
            rating = float(rating_text) if rating_text else 0.0

            if not price >= 0 or price == float("inf") or price != price:
                raise ValueError

            if not 0 <= rating <= 5:
                raise ValueError

            if rating == float("inf"):
                raise ValueError

        except (ValueError, OverflowError):
            return render_template(
                "add_products.html",
                error="Укажите корректную цену и рейтинг от 0 до 5"
            )

        new_product = Product(
            name=name,
            price=price,
            image=image or None,
            category=category or None,
            description=description or None,
            rating=rating
        )

        try:
            db.session.add(new_product)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        return redirect("/products")

    return render_template("add_products.html")


@app.route("/buy", methods=["GET", "POST"])
def buy():
    if not login_required():
        return redirect("/login")

    if request.method == "POST":
        card_id = request.form.get("card_id", "").strip()

        try:
            product_id = int(card_id)
        except (ValueError, TypeError):
            return "Invalid product ID", 400

        product = Product.query.get_or_404(product_id)

        return render_template(
            "buy.html",
            product=product
        )

    return redirect("/cart")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    app.run(debug=True)
