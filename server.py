from operator import ge
from flask import Flask, jsonify, render_template, request, url_for, redirect, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/maggie/Documents/Portafolio/cafe website/cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
app.app_context().push()

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts = db.relationship('Post', backref='author', lazy=True)
#db.create_all()


class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)
    posts = db.relationship('Post', backref='cafe', lazy=True)
# db.create_all()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    coffee_id = db.Column(db.Integer,db.ForeignKey("cafe.id"),nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    user_post = db.Column(db.String(250), nullable=False)
#db.create_all()


@app.route("/")
def home():   
    cafes = db.session.query(Cafe).all()
    all = []
    for cafe in cafes:
        cafe = {
        "id": cafe.id,
        "name": cafe.name,
        "map_url":cafe.map_url,
        "img_url": cafe.img_url,
        "location": cafe.location,
        "seats": cafe.seats,
        "has_toilet": cafe.has_toilet,
        "has_wifi": cafe.has_wifi,
        "has_sockets": cafe.has_sockets,
        "can_take_calls": cafe.can_take_calls,
        "coffee_price": cafe.coffee_price,  
        }
        all.append(cafe)
    return render_template("index.html",cafes=all)


@app.route("/cafes/<int:cafe_id>")
def view_cafe(cafe_id):
    cafe = db.get_or_404(Cafe, cafe_id)
    posts = Post.query.filter_by(coffee_id=cafe_id).all()
    all_posts = []
    for post in posts:
        post = {
        "id": post.id,
        "coffee_id": post.coffee_id,
        "user_id":post.user_id,
        "user_post": post.user_post,
        }
        all_posts.append(post)
    return render_template("cafe.html", cafe=cafe, all_posts =all_posts)


@app.route('/register', methods=["GET","POST"])
def register():
    if request.method == "POST":
        hash_pwd = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8)
        
        u_name = request.form["name"]
        u_email = request.form["email"]
        u_password = request.form["password"]
        new_user = User(email=u_email, password=hash_pwd,name=u_name)
        db.session.add(new_user)
        db.session.commit() 
    return render_template("login.html")


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]   
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", current_user=current_user)
 
    
@app.route("/create_post", methods=["POST"])
def create_post():
    
    content = request.form.get("content")
    cafe_id = request.form.get("cafe_id")
    user_id = request.form.get("user_id")
    cafe = Cafe.query.get(cafe_id)
    user = User.query.get(user_id)
    if cafe is None or user is None:
        return jsonify({"error": "Invalid cafe_id or user_id"}), 400
    new_post = Post(user_post=content, coffee_id=cafe, user_id=user)
    db.session.add(new_post)
    db.session.commit()
    return redirect(url_for("view_cafe",cafe_id=cafe.id) )

      
@app.route("/add", methods=["POST","GET"])
def add_cafe():
    if request.method == "POST":
        new_cafe = Cafe(
            name=request.form.get("name"),
            map_url=request.form.get("map_url"),
            img_url=request.form.get("img_url"),
            location=request.form.get("loc"),
            has_sockets=bool(request.form.get("sockets")),
            has_toilet=bool(request.form.get("toilet")),
            has_wifi=bool(request.form.get("wifi")),
            can_take_calls=bool(request.form.get("calls")),
            seats=request.form.get("seats"),
            coffee_price=request.form.get("coffee_price"),
        )
        db.session.add(new_cafe)
        db.session.commit()
    return render_template("add_cafe.html")


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/closed/<int:cafe_id>", methods=["DELETE","GET"])
def delete_cafe(cafe_id):
    api_key = request.args.get("api-key")
    if api_key == "Hotcake":
        cafe = db.session.query(Cafe).filter_by(id=cafe_id).first()
        if cafe:
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(response={"success": "Successfully deleted the cafe from the database."}), 200
        else:
            return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
    else:
        return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api_key."}), 403    


if __name__ == '__main__':
    app.run(debug=True)
    