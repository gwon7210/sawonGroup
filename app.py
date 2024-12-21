from flask import Flask, render_template, request, redirect, url_for, flash

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

@app.route("/", methods=["GET", "POST"])
def name_entry():
    if request.method == "POST":
        name = request.form.get("name")
        if name in valid_names:
            return redirect(url_for("select_date", name=name))
        else:
            flash("등록된 사용자가 아닙니다.")
    return render_template("name_entry.html")

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

