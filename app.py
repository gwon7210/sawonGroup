from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy.dialects.postgresql import JSON  # PostgreSQL의 JSON 타입 사용

app = Flask(__name__)
app.secret_key = "your_secret_key"

# PostgreSQL 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://noah:password@localhost:5432/sawongroup'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "name_entry"  # 로그인되지 않은 사용자가 접근 시 리디렉션할 뷰

# Flask-Login 사용자 모델 정의
class User(UserMixin, db.Model):  # UserMixin 추가
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=True)
    employee_number = db.Column(db.String(20), nullable=True)

    def get_id(self):
        return str(self.id)  # 사용자 고유 ID 반환

# Vote 모델 정의
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)

# Restaurant 모델 정의
class Restaurant(db.Model):
    link = db.Column(db.String(200), primary_key=True, nullable=False)  # 고유키로 설정
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    votes = db.Column(db.Integer, default=0)
    voters = db.Column(db.String, default="")

# 데이터베이스 초기화
with app.app_context():
    db.drop_all()
    db.create_all()
    # 기본 데이터 추가
    default_users = [
        {"name": "김상은", "employee_number": "172"},
        {"name": "김서정", "employee_number": "293"},
        {"name": "이찬", "employee_number": "185"},
        {"name": "황유림", "employee_number": "042"},
        {"name": "이현아", "employee_number": "025"},
        {"name": "유정화", "employee_number": "051"},
        {"name": "박종현", "employee_number": "175"},
        {"name": "김지수", "employee_number": "071"},
        {"name": "박지원", "employee_number": "174"},
        {"name": "임하경", "employee_number": "226"}
    ]

    for user_data in default_users:
        if not User.query.filter_by(name=user_data["name"]).first():
            user = User(name=user_data["name"], employee_number=user_data["employee_number"], status=None)
            db.session.add(user)
    db.session.commit()

# 로그인 관리자 콜백
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/logout")
@login_required
def logout():
    logout_user()  # 사용자 로그아웃
    flash("로그아웃되었습니다.")
    return redirect(url_for("name_entry"))


@app.route("/", methods=["GET", "POST"])
def name_entry():
    if request.method == "POST":
        name = request.form.get("name")
        employee_number = request.form.get("employee_number")

        # 사용자 정보 조회
        user = User.query.filter_by(name=name, employee_number=employee_number).first()

        if user:
            login_user(user)  # 사용자 로그인
            return redirect(url_for("participation_choice"))
        else:
            flash("사용자 정보를 찾을 수 없습니다.")
            return redirect(url_for("name_entry"))

    return render_template("name_entry.html")


@app.route("/participation_choice", methods=["GET", "POST"])
@login_required  # 로그인된 사용자만 접근 가능
def participation_choice():
    if request.method == "POST":
        choice = request.form.get("choice")
        current_user.status = choice  # 현재 사용자 상태 업데이트
        db.session.commit()  # 데이터베이스에 변경사항 저장
        if current_user.status == "not_participate":
            return render_template("goodbye.html")

        return redirect(url_for("select_date"))
    
    # 케이스별 참여 여부 선택 페이지 분기
    if current_user.status is None:
        return render_template("non_participation.html")

    elif current_user.status == "not_participate":
        return render_template("not_participation.html")

    elif current_user.status == "participate":
        return render_template("participation.html")


@app.route("/select_date", methods=["GET", "POST"])
@login_required  # 로그인된 사용자만 접근 가능
def select_date():
    if request.method == "POST":
        selected_dates = request.form.getlist("dates")
        if selected_dates:
            # 기존 사용자의 투표 삭제
            Vote.query.filter_by(user_id=current_user.id).delete()

            # 새로운 투표 추가
            for date in selected_dates:
                vote = Vote(user_id=current_user.id, date=date)
                db.session.add(vote)
            db.session.commit()

            flash("날짜 투표가 적용되었습니다.")
        else:
            flash("날짜를 먼저 선택하세요.")

    # 날짜별 참여자 수와 이름 계산
    availability = {}
    for day in range(17, 32):
        date_str = f"2024-12-{day:02d}"
        votes = Vote.query.filter_by(date=date_str).all()
        voters = [User.query.get(vote.user_id).name for vote in votes]
        availability[date_str] = {"count": len(voters), "voters": voters}

    return render_template("select_date.html", name=current_user.name, availability=availability)


@app.route("/recommend_restaurant", methods=["GET", "POST"])
@login_required
def recommend_restaurant():
    if request.method == "POST":
        restaurant_names = request.form.getlist("restaurant_name")  # 식당 이름 가져오기
        restaurant_links = request.form.getlist("restaurant_link")
        restaurant_types = request.form.getlist("restaurant_type")

        # 식당 정보 저장
        for rname, link, rtype in zip(restaurant_names, restaurant_links, restaurant_types):
            if rname and link and rtype:
                existing_restaurant = Restaurant.query.filter_by(link=link).first()
                if not existing_restaurant:
                    new_restaurant = Restaurant(name=rname, link=link, type=rtype)
                    db.session.add(new_restaurant)
        db.session.commit()
        return redirect(url_for("vote_restaurant"))
    return render_template("recommend_restaurant.html", name=current_user.name)


@app.route("/vote_restaurant", methods=["GET", "POST"])
@login_required
def vote_restaurant():

    if request.method == "POST":
        selected_restaurant_link = request.form.get("selected_restaurant")
        selected_restaurant = Restaurant.query.get(selected_restaurant_link)

        if selected_restaurant:
            
            if current_user.name in selected_restaurant.voters.split(","):
                selected_restaurant.votes -= 1
                voters_list = selected_restaurant.voters.split(",")
                voters_list.remove(current_user.name)
                selected_restaurant.voters = ",".join(voters_list)
            else:
                selected_restaurant.votes += 1
                voters_list = selected_restaurant.voters.split(",") if selected_restaurant.voters else []
                voters_list.append(current_user.name)
                selected_restaurant.voters = ",".join(voters_list)
            db.session.commit()
            print("After commit and refresh:", selected_restaurant.voters)

        return redirect(url_for("vote_restaurant", name=current_user.name))

    sorted_restaurants = Restaurant.query.order_by(Restaurant.votes.desc()).all()

    return render_template(
        "vote_restaurant.html", name=current_user.name, restaurants=sorted_restaurants
    )

if __name__ == "__main__":
    app.run(debug=True)
