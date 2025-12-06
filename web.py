from flask import Flask, redirect, url_for, render_template, request, session, flash
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from os import path

app = Flask(__name__)
app.config["SECRET_KEY"] = "webapp"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///user.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.permanent_session_lifetime = timedelta(days=7)

db = SQLAlchemy(app)

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    product_name = db.Column(db.String(100))
    product_image = db.Column(db.String(200))
    product_price = db.Column(db.Float)
    quantity = db.Column(db.Integer, default=1)

    def __init__(self, user_id, product_name, product_image, product_price, quantity):
        self.user_id = user_id
        self.product_name = product_name
        self.product_image = product_image
        self.product_price = product_price
        self.quantity = quantity

class Laptop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    screen = db.Column(db.String(100))
    ram = db.Column(db.String(50))
    rom = db.Column(db.String(100))
    chip = db.Column(db.String(100))
    card = db.Column(db.String(100))
    price = db.Column(db.Float, nullable=False)

    def __init__(self, name, image, screen, ram, rom, chip, card, price):
        self.name = name
        self.image = image
        self.screen = screen
        self.ram = ram
        self.rom = rom
        self.chip = chip
        self.card = card
        self.price = price


@app.route("/")
@app.route("/home")
def home():
    laptops = Laptop.query.all()
    return render_template("home.html", laptops=laptops)

@app.route('/register', methods=["POST", "GET"])
def register():
    if request.method == "POST":
        user_name = request.form["name"]
        user_email = request.form["email"]
        user_password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if user_password != confirm_password:
            flash("Nhập lại mật khẩu không chính xác!", "danger")
            return redirect(url_for("register"))

        existing_user = User.query.filter_by(email=user_email).first()
        if existing_user:
            flash("Email đã được sử dụng!", "danger")
            return redirect(url_for("register"))

        new_user = User(name=user_name, email=user_email, password=user_password)
        db.session.add(new_user)
        db.session.commit()

        session.permanent = True
        session["user"] = user_name
        return redirect(url_for("welcome"))

    return render_template("register.html")

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user_email = request.form["email"]
        user_password = request.form["password"]
        
        user = User.query.filter_by(email=user_email).first()
        if user and user.password == user_password:
            session.permanent = True
            session["user"] = user.name
            return redirect(url_for("welcome"))
        else:
            flash("Địa chỉ email hoặc mật khẩu không đúng!", "danger")

    return render_template("login.html")

@app.route("/logout")
def log_out():
    session.pop("user", None)
    flash("Đăng xuất thành công!", "info")
    return redirect(url_for("home"))

@app.route("/cart")
def cart():
    user_name = session["user"]
    user = User.query.filter_by(name=user_name).first()

    if user is None:
        flash("Người dùng không tồn tại!", "danger")
        return redirect(url_for("log_out"))

    cart_items = Cart.query.filter_by(user_id=user.user_id).all()

    total_price = sum(item.product_price * item.quantity for item in cart_items)

    return render_template("cart.html", cart_items=cart_items, total_price=total_price)



@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    if "user" not in session:
        flash("Bạn cần đăng nhập để thêm sản phẩm vào giỏ hàng!", "danger")
        return redirect(url_for("login"))

    user = User.query.filter_by(name=session["user"]).first()
    product_name = request.form["product_name"]
    product_image = request.form["product_image"]
    product_price = float(request.form["product_price"])
    quantity = int(request.form.get("quantity", 1))

    existing_item = Cart.query.filter_by(user_id=user.user_id, product_name=product_name).first()
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = Cart(user_id=user.user_id, product_name=product_name, product_image=product_image,
                        product_price=product_price, quantity=quantity)
        db.session.add(new_item)

    db.session.commit()
    flash("Sản phẩm đã được thêm vào giỏ hàng!", "success")
    return redirect(url_for("cart"))


@app.route("/remove_from_cart/<int:item_id>")
def remove_from_cart(item_id):
    if "user" not in session:
        return redirect(url_for("login"))

    item = Cart.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Sản phẩm đã được xóa khỏi giỏ hàng!", "success")
    return redirect(url_for("cart"))

@app.route("/update_cart/<int:item_id>", methods=["POST"])
def update_cart(item_id):
    if "user" not in session:
        return redirect(url_for("login"))

    quantity = int(request.form["quantity"])
    item = Cart.query.get(item_id)
    if item and quantity > 0:
        item.quantity = quantity
        db.session.commit()
        flash("Cập nhật số lượng thành công!", "success")
    return redirect(url_for("cart"))


@app.route("/welcome")
def welcome():
    if "user" in session:
        name = session["user"]
        return render_template("welcome.html", user=name)
    else:
        return redirect(url_for("login"))



@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form["password"]
        if password == "2345":
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Mật khẩu không đúng!", "danger")

    return render_template("admin_login_form.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if session.get("admin_logged_in"):
        users = User.query.all()
        laptops = Laptop.query.all()
        return render_template("admin.html", users=users, laptops=laptops)
    else:
        return redirect(url_for("admin"))


@app.route("/admin/add", methods=["POST"])
def add_user():
    if session.get("admin_logged_in"):
        user_name = request.form["name"]
        user_email = request.form["email"]
        user_password = request.form["password"]

        existing_user = User.query.filter_by(email=user_email).first()
        if existing_user:
            flash("Email đã được sử dụng!", "danger")
            return redirect(url_for("admin"))

        new_user = User(name=user_name, email=user_email, password=user_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Thêm người dùng thành công!", "success")
        return redirect(url_for("admin"))
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin/edit/<int:user_id>", methods=["POST", "GET"])
def edit_user(user_id):
    if session.get("admin_logged_in"):
        user = User.query.get(user_id)
        if request.method == "POST":
            user.name = request.form["name"]
            user.email = request.form["email"]
            user.password = request.form["password"]
            db.session.commit()
            flash("Cập nhật người dùng thành công!", "success")
            return redirect(url_for("admin"))
        
        return render_template("edit_user.html", user=user)
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin/delete/<int:user_id>")
def delete_user(user_id):
    if session.get("admin_logged_in"):
        user = User.query.get(user_id)
        if user:
            Cart.query.filter_by(user_id=user.user_id).delete()
            db.session.delete(user)
            db.session.commit()
            flash("Xóa người dùng thành công!", "success")
        else:
            flash("Người dùng không tồn tại!", "danger")
        return redirect(url_for("admin_dashboard"))
    else:
        return redirect(url_for("admin"))

@app.route("/admin/edit_laptop/<int:laptop_id>", methods=["POST", "GET"])
def edit_laptop(laptop_id):
    if session.get("admin_logged_in"):
        laptop = Laptop.query.get(laptop_id)
        if request.method == "POST":
            laptop.name = request.form["name"]
            laptop.image = request.form["image"]
            laptop.screen = request.form["screen"]
            laptop.ram = request.form["ram"]
            laptop.rom = request.form["rom"]
            laptop.chip = request.form["chip"]
            laptop.card = request.form["card"]
            laptop.price = float(request.form["price"])
            db.session.commit()
            flash("Cập nhật thông tin laptop thành công!", "success")
            return redirect(url_for("admin_dashboard"))
        
        return render_template("edit_laptop.html", laptop=laptop)
    else:
        return redirect(url_for("admin"))

@app.route("/admin/delete_laptop/<int:laptop_id>")
def delete_laptop(laptop_id):
    if session.get("admin_logged_in"):
        laptop = Laptop.query.get(laptop_id)
        db.session.delete(laptop)
        db.session.commit()
        flash("Xóa laptop thành công!", "success")
        return redirect(url_for("admin_dashboard"))
    else:
        return redirect(url_for("admin"))


def add_sample_data():
    if Laptop.query.count() == 0:
        laptops = [
            Laptop("Laptop ASUS TUF Gaming A15", "static/images/laptop_a.webp", "15.6 inch Full HD", "8 GB", "512 GB SSD", "AMD Ryzen 5 7535HS", "NVIDIA RTX 3050", 1500),
            Laptop("Laptop Lenovo LOQ 15IAX9", "static/images/laptop_b.webp", "15.6 inch Full HD 144 Hz", "8 GB", "512 GB SSD", "Intel Core i5-12450HX", "NVIDIA GTX 3050", 1200),
            Laptop("Apple MacBook Air M2 2022", "static/images/laptop_c.webp", "13.6 inch", "8 GB", "256 GB SSD", "Apple M2", "8 nhân GPU", 1600),
            Laptop("Laptop ASUS Zenbook S 14 OLED", "static/images/laptop_d.webp", "14 inch 3K", "32 GB", "1 TB SSD", "Intel Core Ultra 7-258V", "Intel Arc Graphics", 2000),
        ]
        db.session.bulk_save_objects(laptops)
        db.session.commit()
        print("Sample data added.")



if __name__ == "__main__":
    if not path.exists("user.db"):
        with app.app_context():
            db.create_all()
            add_sample_data()
            print("Created database and added sample data.")
    app.run(debug=True)

