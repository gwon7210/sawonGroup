from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask.json import jsonify  # flask.json에서 명시적으로 가져옴

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 허용된 이름 리스트
valid_names = ["김상은", "김서정", "이찬", "황유림", "이현아", "유정화", "박종현", "김지수", "박지원", "임하경" ]
# 각 날짜별 투표 내역
votes = {}

# 각 날짜별 가능한 사람 수
availability = {f"2024-12-{day:02d}": 0 for day in range(17, 32)}

# 식당 추천 및 투표
restaurants = []  # [{"link": "http://example.com", "type": "중식당", "votes": 0, "voters": []}]
restaurant_votes = {}

#DB
# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///user_status.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 데이터베이스 모델 정의
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=True)  # 상태값: "participate", "not_participate", 또는 None
    employee_number = db.Column(db.String(20), nullable=True)  # 사내번호

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

user_status = {}

@app.route("/", methods=["GET", "POST"])
def name_entry():
    if request.method == "POST":
        name = request.form.get("name")
        employee_number = request.form.get("employee_number")

        # 사용자 정보 조회
        user = User.query.filter_by(name=name, employee_number=employee_number).first()

        if user:
            if user.status == "not_participate":
                flash("현재 '미참여' 상태입니다. 변경하시겠습니까?")
            elif user.status == "participate":
                flash("현재 '참여' 상태입니다. 변경하시겠습니까?")
            elif user.status is None:
                flash("참석 여부를 말해주세요")
            return redirect(url_for("participation_choice"))
        else:
            flash("사용자 정보를 찾을 수 없습니다.")
            return redirect(url_for("name_entry"))

    return render_template("name_entry.html")


@app.route("/participation_choice", methods=["GET", "POST"])
def participation_choice():
    if request.method == "POST":
        # POST 요청에 대한 처리 (예: 상태 변경)
        choice = request.form.get("choice")

        # 완료 후 다시 선택 페이지로 리디렉션
        return redirect(url_for("participation_choice"))

    return render_template("participation_choice.html")



# @app.route("/participation_choice/<name>", methods=["GET", "POST"])
# def participation_choice(name):
#     if request.method == "POST":
#         choice = request.form.get("choice")
#         if choice == "participate":
#             user_status[name] = "participate"
#             flash("참여 상태로 변경되었습니다.")
#             return redirect(url_for("select_date", name=name))
#         elif choice == "not_participate":
#             user_status[name] = "not_participate"
#             flash("미참여 상태로 변경되었습니다.")
#             return redirect(url_for("name_entry"))
#     current_status = user_status.get(name, "none")  # 현재 상태 가져오기
#     return render_template("participation_choice.html", name=name, current_status=current_status)




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

