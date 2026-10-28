import json
import os
from functools import wraps
import bcrypt
import mysql.connector
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from config import Config
from analytics import clean_dataset, generate_dashboard, profile_dataset, read_dataset
from beauty_api import (
    get_beauty_product,
    save_product_to_database,
    search_beauty_products,
)

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}


def get_db():
    return mysql.connector.connect(
        host=app.config["DB_HOST"],
        user=app.config["DB_USER"],
        password=app.config["DB_PASSWORD"],
        database=app.config["DB_NAME"],
    )


def login_required(route):
    @wraps(route)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return route(*args, **kwargs)

    return wrapped


def current_dataset():
    path = session.get("dataset_path")
    extension = session.get("dataset_extension")
    if not path or not os.path.exists(path):
        return None
    return read_dataset(path, extension)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def cache_beauty_products(products):
    """Save API records locally and attach their local ID for detail links."""
    if not products:
        return products
    try:
        db = get_db()
        cursor = db.cursor()
        for product in products:
            product["id"] = save_product_to_database(cursor, product)
        db.commit()
        cursor.close()
        db.close()
    except mysql.connector.Error:
        # Search results remain usable even when local caching is unavailable.
        for product in products:
            product["id"] = None
    return products


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/beauty-products", methods=["GET", "POST"])
@login_required
def beauty_products():
    keyword = request.values.get("keyword", "").strip()
    brand = request.values.get("brand", "").strip()
    category = request.values.get("category", "").strip()
    barcode = request.values.get("barcode", "").strip()
    products = []
    error = None
    searched = bool(keyword or brand or category or barcode)
    if barcode:
        product, error = get_beauty_product(
            barcode,
            app.config["BEAUTY_API_BASE"],
            app.config["BEAUTY_API_USER_AGENT"],
            app.config["BEAUTY_API_TIMEOUT"],
        )
        products = cache_beauty_products([product]) if product else []
    elif keyword or brand or category:
        products, error = search_beauty_products(
            keyword,
            brand,
            category,
            app.config["BEAUTY_API_BASE"],
            app.config["BEAUTY_API_USER_AGENT"],
            timeout=app.config["BEAUTY_API_TIMEOUT"],
        )
        products = cache_beauty_products(products)
    return render_template(
        "beauty_products.html",
        products=products,
        searched=searched,
        error=error,
        filters={
            "keyword": keyword,
            "brand": brand,
            "category": category,
            "barcode": barcode,
        },
    )


@app.route("/beauty-products/<int:product_id>")
@login_required
def product_detail(product_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM beauty_products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        db.close()
        if not product:
            return not_found(None)
        available_fields = [
            "product_name",
            "brand",
            "category",
            "description",
            "ingredients",
            "quantity",
            "countries",
            "image_url",
        ]
        known_count = sum(1 for field in available_fields if product.get(field))
        product["completeness"] = round((known_count / len(available_fields)) * 100)
        return render_template("product_detail.html", product=product)
    except mysql.connector.Error:
        flash(
            "Could not load this cached product. Please try searching again.", "danger"
        )
        return redirect(url_for("beauty_products"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email = (
            request.form.get("name", "").strip(),
            request.form.get("email", "").strip().lower(),
        )
        password, confirm = request.form.get("password", ""), request.form.get(
            "confirm_password", ""
        )
        if not name or not email or len(password) < 6 or password != confirm:
            flash(
                "Enter a name and email; passwords must match and be at least 6 characters.",
                "danger",
            )
            return render_template("register.html")
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                flash("An account with this email already exists.", "danger")
            else:
                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed),
                )
                db.commit()
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("login"))
            cursor.close()
            db.close()
        except mysql.connector.Error:
            flash(
                "Could not connect to MySQL. Check your .env database settings.",
                "danger",
            )
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            db = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (request.form.get("email", "").strip().lower(),),
            )
            user = cursor.fetchone()
            cursor.close()
            db.close()
            if user and bcrypt.checkpw(
                request.form.get("password", "").encode(), user["password"].encode()
            ):
                session.clear()
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                return redirect(url_for("dashboard"))
            flash("Invalid email or password.", "danger")
        except mysql.connector.Error:
            flash(
                "Could not connect to MySQL. Check your .env database settings.",
                "danger",
            )
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("dataset")
        if not file or not file.filename or not allowed_file(file.filename):
            flash("Choose a valid CSV, XLSX, or XLS file.", "danger")
            return render_template("upload.html")
        filename = secure_filename(file.filename)
        extension = filename.rsplit(".", 1)[1].lower()
        path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{session['user_id']}_{filename}"
        )
        file.save(path)
        try:
            data = read_dataset(path, extension)
            if (
                len(data) > app.config["MAX_ROWS"]
                or len(data.columns) > app.config["MAX_COLUMNS"]
            ):
                raise ValueError(
                    f"Limit is {app.config['MAX_ROWS']:,} rows and {app.config['MAX_COLUMNS']} columns."
                )
            (
                session["dataset_path"],
                session["dataset_extension"],
                session["dataset_name"],
            ) = (path, extension, filename)
            session.pop("cleaning", None)
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                "INSERT INTO datasets (user_id, file_name, file_type, row_count, column_count) VALUES (%s,%s,%s,%s,%s)",
                (session["user_id"], filename, extension, len(data), len(data.columns)),
            )
            dataset_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO analysis_history (dataset_id, summary_data) VALUES (%s, %s)",
                (dataset_id, json.dumps(profile_dataset(data), default=str)),
            )
            db.commit()
            cursor.close()
            db.close()
            session["dataset_id"] = dataset_id
            flash("Dataset uploaded and profiled successfully.", "success")
            return redirect(url_for("data_profile"))
        except (ValueError, Exception) as error:
            if os.path.exists(path):
                os.remove(path)
            flash(f"The file could not be analyzed: {str(error)}", "danger")
    return render_template("upload.html")


@app.route("/data-profile")
@login_required
def data_profile():
    data = current_dataset()
    if data is None:
        flash("Upload a dataset first.", "warning")
        return redirect(url_for("upload"))
    return render_template(
        "data_profile.html",
        profile=profile_dataset(data),
        dataset_name=session.get("dataset_name"),
    )


@app.route("/cleaning", methods=["GET", "POST"])
@login_required
def cleaning():
    data = current_dataset()
    if data is None:
        return redirect(url_for("upload"))
    cleaned, summary = clean_dataset(data)
    if request.method == "POST":
        cleaned.to_pickle(session["dataset_path"] + ".cleaned")
        session["cleaning"] = True
        flash("Cleaning has been applied to this dashboard session.", "success")
        return redirect(url_for("dashboard"))
    return render_template(
        "cleaning.html", summary=summary, dataset_name=session.get("dataset_name")
    )


@app.route("/dashboard")
@login_required
def dashboard():
    data = current_dataset()
    if data is None:
        return render_template("dashboard.html", analysis=None)
    clean_path = session.get("dataset_path", "") + ".cleaned"
    if session.get("cleaning") and os.path.exists(clean_path):
        data = __import__("pandas").read_pickle(clean_path)
    return render_template(
        "dashboard.html",
        analysis=generate_dashboard(data),
        dataset_name=session.get("dataset_name"),
    )


@app.route("/analysis")
@login_required
def analysis():
    return redirect(url_for("dashboard"))


@app.route("/history")
@login_required
def history():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, file_name, file_type, row_count, column_count, uploaded_at FROM datasets WHERE user_id = %s ORDER BY uploaded_at DESC",
            (session["user_id"],),
        )
        rows = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template("history.html", datasets=rows)
    except mysql.connector.Error:
        flash("Could not load history from MySQL.", "danger")
        return render_template("history.html", datasets=[])


@app.route("/history/<int:dataset_id>")
@login_required
def history_detail(dataset_id):
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT d.file_name, d.file_type, d.row_count, d.column_count, d.uploaded_at, h.summary_data FROM datasets d JOIN analysis_history h ON h.dataset_id = d.id WHERE d.id = %s AND d.user_id = %s ORDER BY h.created_at DESC LIMIT 1",
            (dataset_id, session["user_id"]),
        )
        item = cursor.fetchone()
        cursor.close()
        db.close()
        if not item:
            return not_found(None)
        item["profile"] = json.loads(item["summary_data"])
        return render_template(
            "history_detail.html", item=item, dataset_name=item["file_name"]
        )
    except mysql.connector.Error:
        flash("Could not load this saved analysis.", "danger")
        return redirect(url_for("history"))


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(413)
def too_large(error):
    flash("This file is larger than the allowed upload size.", "danger")
    return redirect(url_for("upload"))


@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
