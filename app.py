from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('mongodb://3.34.190.41', 27017, username="test", password="test")
db = client.challenge


@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})

        return render_template('index.html', user_info = user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@app.route('/apply')
def apply():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        return render_template('apply.html')
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/mypage/<username>')
def mypage(username):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])

        user_info = db.users.find_one({"username": payload["id"]})

        return render_template('mypage.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 나의 포스트 불러오기 api
@app.route('/api/mypage/<username>', methods=['GET'])
def api_my_apply(username):
    challenges = list(db.challenge.find({'username': username}, {'_id': False}))
    return jsonify({'result': 'success', 'challenges': challenges})






@app.route("/api/challenges", methods=["POST"])
def apply_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        image_receive = request.form['image_give']
        title_receive = request.form['title_give']
        content_receive = request.form['content_give']

        challenge_list = list(db.challenge.find({}, {'_id': False}))
        count = len(challenge_list) + 1

        doc = {
            "username": user_info["username"],
            'image': image_receive,
            'title': title_receive,
            'content': content_receive,
            'count' : count
        }
        db.challenge.insert_one(doc)

        return jsonify({'msg': '등록 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route("/challenge/delete", methods=["POST"])
def challenge_delete():
    num_receive = request.form['num_give']
    db.challenge.delete_one({'count': int(num_receive)})
    return jsonify({'msg': '삭제완료'})

@app.route("/api/challenges", methods=["GET"])
def challenge_get():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        challenge_list = list(db.challenge.find({}, {'_id': False}))
        return jsonify({'challenges': challenge_list})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash  # 비밀번호
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


#########################

# @app.route('/mypage/<username>')
# def mypage(username):
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         status = (username == payload["id"])
#
#         user_info = db.challenge.find_one({"username": username}, payload["id"])
#         return render_template('mypage.html',user_info=user_info)
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)