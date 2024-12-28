from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_status.db'
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

# 데이터베이스 초기화
with app.app_context():
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
        return redirect(url_for("participation_choice"))
    
    # 케이스별 참여 여부 선택 페이지 분기
    if current_user.status is None:
        return render_template("non_participation.html")

    elif current_user.status == "not_participate":
        return render_template("not_participation.html")

    elif current_user.status == "participate":
        return render_template("participation.html")

@app.route("/select_date/<name>", methods=["GET", "POST"])
def select_date(name):
    if request.method == "POST":
        selected_dates = request.form.getlist("dates")
        if selected_dates:
            # 날짜 선택 저장
            if name in votes:
                for date in votes[name]:
                    availability[date] -= 1
                votes[name] = []  # 이전 투표 초기화
            votes[name] = selected_dates
            for date in selected_dates:
                availability[date] += 1
            flash("날짜 투표가 적용되었습니다.")
        else:
            flash("날짜를 먼저 선택하세요.")
    return render_template("select_date.html", name=name, availability=availability)

@app.route("/recommend_restaurant/<name>", methods=["GET", "POST"])
def recommend_restaurant(name):
    if request.method == "POST":
        restaurant_names = request.form.getlist("restaurant_name")  # 식당 이름 가져오기
        restaurant_links = request.form.getlist("restaurant_link")
        restaurant_types = request.form.getlist("restaurant_type")

        # 식당 정보 저장
        for rname, link, rtype in zip(restaurant_names, restaurant_links, restaurant_types):
            if rname and link and rtype and link not in restaurant_votes:
                restaurant_votes[link] = {
                    "name": rname,  # 식당 이름 저장
                    "link": link,
                    "type": rtype,
                    "votes": 0,
                    "voters": [],
                }
                restaurants.append(restaurant_votes[link])
        return redirect(url_for("vote_restaurant", name=name))
    return render_template("recommend_restaurant.html", name=name)

@app.route("/vote_restaurant/<name>", methods=["GET", "POST"])
def vote_restaurant(name):
    if request.method == "POST":
        selected_restaurant = request.form.get("selected_restaurant")
        if selected_restaurant in restaurant_votes:
            if name in restaurant_votes[selected_restaurant]["voters"]:
                restaurant_votes[selected_restaurant]["votes"] -= 1
                restaurant_votes[selected_restaurant]["voters"].remove(name)
            else:
                restaurant_votes[selected_restaurant]["votes"] += 1
                restaurant_votes[selected_restaurant]["voters"].append(name)
        return redirect(url_for("vote_restaurant", name=name))
    sorted_restaurants = sorted(
        restaurants, key=lambda r: (-r["votes"], r["link"])
    )
    return render_template(
        "vote_restaurant.html", name=name, restaurants=sorted_restaurants
    )

if __name__ == "__main__":
    app.run(debug=True)

