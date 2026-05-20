import base64
import json
import os
import socket
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite:///{Path(INSTANCE_DIR, 'cafeteria_virtual.db').as_posix()}"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cafeteria-secreta")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    DEFAULT_SQLITE_URL,
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")


def make_placeholder_svg(title, bg, fg="#ffffff"):
    svg = f'''
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="600" viewBox="0 0 900 600">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="{bg}"/>
          <stop offset="100%" stop-color="#111827"/>
        </linearGradient>
      </defs>
      <rect width="900" height="600" rx="48" fill="url(#g)"/>
      <circle cx="730" cy="140" r="120" fill="rgba(255,255,255,0.14)"/>
      <circle cx="160" cy="470" r="150" fill="rgba(255,255,255,0.08)"/>
      <text x="70" y="220" fill="{fg}" font-size="72" font-family="Arial, sans-serif" font-weight="700">{title}</text>
      <text x="70" y="290" fill="rgba(255,255,255,0.88)" font-size="30" font-family="Arial, sans-serif">Cafetería virtual</text>
    </svg>
    '''
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def parse_json_text(value, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def money(value):
    return f"${value:,.0f}".replace(",", ".")


def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def csv_from_json_text(value):
    parsed = parse_json_text(value, [])
    if isinstance(parsed, list):
        return ", ".join(str(item) for item in parsed)
    return ""


def product_form_values(product=None):
    if not product:
        return {
            "product_id": "",
            "name": "",
            "description": "",
            "category": "calientes",
            "image_url": "",
            "price": "",
            "discount_price": "",
            "ingredients": "",
            "leche_options": "",
            "harina_options": "",
            "extra_options": "",
            "exhausted": False,
        }

    ingredient_options = parse_json_text(product.ingredient_options, {})
    return {
        "product_id": product.id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "image_url": product.image_url,
        "price": product.price,
        "discount_price": product.discount_price or "",
        "ingredients": csv_from_json_text(product.ingredients),
        "leche_options": ", ".join(ingredient_options.get("leche", [])),
        "harina_options": ", ".join(ingredient_options.get("harina", [])),
        "extra_options": ", ".join(ingredient_options.get("extra", [])),
        "exhausted": product.exhausted,
    }


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="usuario")


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount_price = db.Column(db.Float, nullable=True)
    ingredients = db.Column(db.Text, nullable=False, default="[]")
    ingredient_options = db.Column(db.Text, nullable=False, default="{}")
    exhausted = db.Column(db.Boolean, default=False)
    sold_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    price = db.Column(db.Float, nullable=False)
    units = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_type = db.Column(db.String(40), nullable=False)
    unit_value = db.Column(db.Float, nullable=False)
    sale_value = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    total = db.Column(db.Float, nullable=False)
    expiration_date = db.Column(db.String(40), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(80), nullable=False, default="pedido confirmado")
    payment_method = db.Column(db.String(30), nullable=False)
    dining_option = db.Column(db.String(30), nullable=False)
    total = db.Column(db.Float, nullable=False)
    kitchen_done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("orders", lazy=True))


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=True)
    name_snapshot = db.Column(db.String(140), nullable=False)
    price_snapshot = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    ingredient_notes = db.Column(db.Text, nullable=False, default="{}")

    order = db.relationship("Order", backref=db.backref("items", lazy=True, cascade="all, delete-orphan"))


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def role_required(*roles):
    def decorator(view):
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                return redirect(url_for("login"))
            return view(*args, **kwargs)

        wrapped.__name__ = view.__name__
        return wrapped

    return decorator


def seed_data():
    admin = User.query.filter_by(email="admin@x.com").first()
    if not admin:
        db.session.add(
            User(
                name="Administrador",
                email="admin@x.com",
                password_hash=generate_password_hash("123"),
                role="admin",
            )
        )

    cook = User.query.filter_by(email="cocina@x.com").first()
    if not cook:
        db.session.add(
            User(
                name="Cocinero",
                email="cocina@x.com",
                password_hash=generate_password_hash("123"),
                role="cocina",
            )
        )

    if Product.query.count() == 0:
        sample_products = [
            {
                "name": "Café Latte",
                "description": "Espresso suave con leche vaporizada y espuma cremosa.",
                "category": "calientes",
                "image_url": make_placeholder_svg("Café Latte", "#6f4e37"),
                "price": 8500,
                "ingredients": ["café", "leche"],
                "ingredient_options": {
                    "leche": ["deslactosada", "descremada", "entera", "almendra"],
                    "extra": ["canela", "vainilla", "caramelo"],
                },
            },
            {
                "name": "Mocaccino Frío",
                "description": "Chocolate, café y hielo para una bebida refrescante.",
                "category": "fríos",
                "image_url": make_placeholder_svg("Mocaccino", "#0f766e"),
                "price": 9800,
                "ingredients": ["café", "chocolate", "hielo"],
                "ingredient_options": {
                    "leche": ["entera", "descremada", "almendra"],
                    "extra": ["crema", "chispas", "jarabe"],
                },
            },
            {
                "name": "Torta de Chocolate",
                "description": "Bizcocho húmedo con ganache y decoración artesanal.",
                "category": "tortas",
                "image_url": make_placeholder_svg("Torta", "#be123c"),
                "price": 12000,
                "ingredients": ["harina", "cacao", "huevo"],
                "ingredient_options": {
                    "harina": ["trigo", "avena", "almendra"],
                    "extra": ["sin azúcar", "normal"],
                },
            },
            {
                "name": "Galletas de Avena",
                "description": "Galletas crocantes con avena y miel.",
                "category": "galletas",
                "image_url": make_placeholder_svg("Galletas", "#b45309"),
                "price": 6000,
                "ingredients": ["avena", "miel"],
                "ingredient_options": {
                    "harina": ["avena", "trigo", "integral"],
                    "leche": ["deslactosada", "entera"],
                },
            },
            {
                "name": "Pan Artesanal",
                "description": "Pan recién horneado, ideal para acompañar cualquier bebida.",
                "category": "panes",
                "image_url": make_placeholder_svg("Pan", "#ca8a04"),
                "price": 4500,
                "ingredients": ["harina", "levadura"],
                "ingredient_options": {
                    "harina": ["trigo", "integral", "centeno"],
                    "extra": ["semillas", "sin sal", "con mantequilla"],
                },
            },
        ]

        for item in sample_products:
            db.session.add(
                Product(
                    name=item["name"],
                    description=item["description"],
                    category=item["category"],
                    image_url=item["image_url"],
                    price=item["price"],
                    ingredients=json.dumps(item["ingredients"], ensure_ascii=False),
                    ingredient_options=json.dumps(item["ingredient_options"], ensure_ascii=False),
                    exhausted=False,
                )
            )

    db.session.commit()


@app.context_processor
def inject_helpers():
    return {"money": money}


@app.route("/")
def index():
    if current_user.is_authenticated:
        if current_user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        if current_user.role == "cocina":
            return redirect(url_for("kitchen"))
        return redirect(url_for("user_dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Ese correo ya existe.", "error")
            return redirect(url_for("register"))

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="usuario",
        )
        db.session.add(user)
        try:
            db.session.commit()
            flash("Registro exitoso. Ahora inicia sesión.", "success")
        except Exception as e:
            db.session.rollback()
            print(f"Error al registrar usuario: {e}")
            flash(f"Error al registrar: {e}", "error")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Correo o contraseña incorrectos.", "error")
            return redirect(url_for("login"))

        login_user(user)
        flash(f"Bienvenida/o, {user.name}.", "success")

        if user.role == "admin":
            return redirect(url_for("admin_dashboard"))
        if user.role == "cocina":
            return redirect(url_for("kitchen"))
        return redirect(url_for("user_dashboard"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.pop("active_order_id", None)
    flash("Sesión cerrada.", "success")
    return redirect(url_for("login"))


@app.route("/user")
@login_required
@role_required("usuario")
def user_dashboard():
    products = Product.query.order_by(Product.category.asc(), Product.name.asc()).all()
    categories = ["calientes", "fríos", "tortas", "galletas", "panes"]
    return render_template(
        "user_dashboard.html",
        products=products,
        categories=categories,
        active_order_id=session.get("active_order_id"),
    )


@app.route("/user/checkout", methods=["POST"])
@login_required
@role_required("usuario")
def user_checkout():
    payload = request.form.get("cart_payload", "[]")
    payment_method = request.form.get("payment_method", "efectivo")
    dining_option = request.form.get("dining_option", "cafeteria")
    cart = parse_json_text(payload, [])

    if not cart:
        flash("Tu carrito está vacío.", "error")
        return redirect(url_for("user_dashboard"))

    order_total = 0
    order = Order(
        user_id=current_user.id,
        status="pedido confirmado",
        payment_method=payment_method,
        dining_option=dining_option,
        total=0,
    )
    db.session.add(order)
    db.session.flush()

    for item in cart:
        product = Product.query.get(item["id"])
        if not product:
            continue
        quantity = int(item.get("quantity", 1))
        price = float(item.get("price", product.price))
        order_total += price * quantity
        db.session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                name_snapshot=item.get("name", product.name),
                price_snapshot=price,
                quantity=quantity,
                ingredient_notes=json.dumps(item.get("ingredients", {}), ensure_ascii=False),
            )
        )
        product.sold_count += quantity

    order.total = order_total
    try:
        db.session.commit()
        session["active_order_id"] = order.id
        socketio.emit("orders_updated", {"message": "Nuevo pedido"})
        if payment_method == "efectivo":
            flash("puedes acercarte a caja y cancelar para continuar con tu orden", "success")
        else:
            flash("Pago por tarjeta: simulación completada.", "success")
        flash("Tu pedido fue creado con éxito.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error al crear pedido: {e}")
        flash(f"Error al guardar pedido: {e}", "error")
    return redirect(url_for("user_tracking"))


@app.route("/user/orders")
@login_required
@role_required("usuario")
def user_tracking():
    order_id = session.get("active_order_id")
    order = Order.query.get(order_id) if order_id else Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).first()
    return render_template(
        "user_orders.html",
        order=order,
        google_maps_key=os.getenv("GOOGLE_MAPS_API_KEY", ""),
    )


@app.route("/user/history")
@login_required
@role_required("usuario")
def user_history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template("user_history.html", orders=orders)


@app.route("/admin")
@login_required
@role_required("admin")
def admin_dashboard():
    products = Product.query.all()
    top = sorted(products, key=lambda item: item.sold_count, reverse=True)[:5]
    bottom = sorted(products, key=lambda item: item.sold_count)[:5]
    return render_template("admin_dashboard.html", top=top, bottom=bottom, products=products)


@app.route("/admin/inventory", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_inventory():
    if request.method == "POST":
        name = request.form["name"]
        price = float(request.form["price"])
        units = float(request.form["units"])
        quantity = float(request.form["quantity"])
        unit_type = request.form["unit_type"]
        unit_value = float(request.form["unit_value"])
        sale_value = float(request.form["sale_value"])
        profit = sale_value - unit_value
        total = quantity * sale_value
        expiration_date = request.form["expiration_date"]

        db.session.add(
            InventoryItem(
                name=name,
                price=price,
                units=units,
                quantity=quantity,
                unit_type=unit_type,
                unit_value=unit_value,
                sale_value=sale_value,
                profit=profit,
                total=total,
                expiration_date=expiration_date,
            )
        )
        try:
            db.session.commit()
            flash("Inventario agregado.", "success")
        except Exception as e:
            db.session.rollback()
            print(f"Error al agregar inventario: {e}")
            flash(f"Error al guardar: {e}", "error")
        return redirect(url_for("admin_inventory"))

    items = InventoryItem.query.order_by(InventoryItem.created_at.desc()).all()
    return render_template("admin_inventory.html", items=items)


@app.route("/admin/products", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_products():
    editing_product = None
    if request.method == "POST":
        product_id = request.form.get("product_id", "").strip()
        name = request.form["name"]
        description = request.form["description"]
        category = request.form["category"]
        image_url = request.form["image_url"].strip() or make_placeholder_svg(name, "#374151")
        price = float(request.form["price"])
        discount_price_raw = request.form.get("discount_price", "").strip()
        discount_price = float(discount_price_raw) if discount_price_raw else None
        ingredients = [item.strip() for item in request.form.get("ingredients", "").split(",") if item.strip()]
        ingredient_options = {
            "leche": [item.strip() for item in request.form.get("leche_options", "").split(",") if item.strip()],
            "harina": [item.strip() for item in request.form.get("harina_options", "").split(",") if item.strip()],
            "extra": [item.strip() for item in request.form.get("extra_options", "").split(",") if item.strip()],
        }
        exhausted = request.form.get("exhausted") == "on"

        if product_id:
            product = Product.query.get_or_404(int(product_id))
            product.name = name
            product.description = description
            product.category = category
            product.image_url = image_url
            product.price = price
            product.discount_price = discount_price
            product.ingredients = json.dumps(ingredients, ensure_ascii=False)
            product.ingredient_options = json.dumps(ingredient_options, ensure_ascii=False)
            product.exhausted = exhausted
            flash("Producto actualizado.", "success")
            socketio.emit("products_updated", {"message": "Producto actualizado"})
        else:
            db.session.add(
                Product(
                    name=name,
                    description=description,
                    category=category,
                    image_url=image_url,
                    price=price,
                    discount_price=discount_price,
                    ingredients=json.dumps(ingredients, ensure_ascii=False),
                    ingredient_options=json.dumps(ingredient_options, ensure_ascii=False),
                    exhausted=exhausted,
                )
            )
            flash("Producto agregado al menú.", "success")
            socketio.emit("products_updated", {"message": "Nuevo producto"})

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error al guardar producto: {e}")
            flash(f"Error al guardar: {e}", "error")
        return redirect(url_for("admin_products"))

    edit_id = request.args.get("edit", type=int)
    if edit_id:
        editing_product = Product.query.get_or_404(edit_id)

    products = Product.query.order_by(Product.category.asc(), Product.name.asc()).all()
    return render_template(
        "admin_products.html",
        products=products,
        editing_product=editing_product,
        form_values=product_form_values(editing_product),
    )


@app.route("/admin/products/<int:product_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.exhausted = not product.exhausted
    try:
        db.session.commit()
        socketio.emit("products_updated", {"message": "Producto actualizado"})
        flash("Estado del producto actualizado.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error al actualizar estado: {e}")
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_products"))


@app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    try:
        db.session.commit()
        socketio.emit("products_updated", {"message": "Producto eliminado"})
        flash("Producto eliminado.", "success")
    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar producto: {e}")
        flash(f"Error: {e}", "error")
    return redirect(url_for("admin_products"))


@app.route("/admin/orders", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_orders():
    if request.method == "POST":
        order_id = int(request.form["order_id"])
        status = request.form["status"]
        order = Order.query.get_or_404(order_id)
        order.status = status
        db.session.commit()
        socketio.emit("order_status_updated", {"order_id": order.id, "status": order.status})
        flash("Estado del pedido actualizado.", "success")
        return redirect(url_for("admin_orders"))

    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin_orders.html", orders=orders)


@app.route("/kitchen")
@login_required
@role_required("cocina")
def kitchen():
    orders = Order.query.filter_by(kitchen_done=False).order_by(Order.created_at.asc()).all()
    return render_template("kitchen.html", orders=orders)


@app.route("/kitchen/<int:order_id>/ready", methods=["POST"])
@login_required
@role_required("cocina")
def kitchen_ready(order_id):
    order = Order.query.get_or_404(order_id)
    order.kitchen_done = True
    order.status = "en camino"
    db.session.commit()
    socketio.emit("order_status_updated", {"order_id": order.id, "status": order.status})
    flash("Pedido marcado como listo.", "success")
    return redirect(url_for("kitchen"))


@app.route("/api/orders/<int:order_id>")
@login_required
def api_order(order_id):
    order = Order.query.get_or_404(order_id)
    if current_user.role == "usuario" and order.user_id != current_user.id:
        return jsonify({"error": "No autorizado"}), 403

    return jsonify(
        {
            "id": order.id,
            "status": order.status,
            "payment_method": order.payment_method,
            "dining_option": order.dining_option,
            "total": order.total,
            "items": [
                {
                    "name": item.name_snapshot,
                    "price": item.price_snapshot,
                    "quantity": item.quantity,
                    "ingredients": parse_json_text(item.ingredient_notes, {}),
                }
                for item in order.items
            ],
        }
    )


with app.app_context():
    db.create_all()
    seed_data()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    lan_ip = get_lan_ip()
    print(f"Servidor local: http://127.0.0.1:{port}")
    print(f"Servidor en red: http://{lan_ip}:{port}")
    socketio.run(app, host="0.0.0.0", port=port, debug=True, allow_unsafe_werkzeug=True)