from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from google.oauth2 import id_token
from google.auth.transport.requests import Request
import yaml
import maketoken
import database
import bcrypt

app = Flask(__name__)
CORS(app)

# secret credentials
creds = yaml.safe_load(open('credentials.yaml'))
app.config['SECRET_KEY'] = creds['APP_SECRET']

# this is the part of user registration (signup)
@app.route("/signup", methods=['POST'])
def signup():
    mysql = database.Database()  # database class object
    payload = request.get_json()
    fname = payload['firstName']
    lname = payload['lastName']
    email_id = payload['emailId']
    password = str(payload['password'])
    q1 = payload['maiden']
    q2 = payload['artist']
    profile = google_id = "dummy"
    # print(fname, lname, email_id, password, password, q1, q2, q3)

    # look for the account, if it already exists
    result = mysql.getUser(email_id)
    if result > 0:
        mysql.closeCursor()
        return jsonify({'message': 'account already exists'}), 403

    # generating the salt and hashing the password with salt
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(bytes, salt)

    # decoding the binary format to store them in the database
    salt = salt.decode('utf-8')
    hashed_password = hashed_password.decode('utf-8')
    # print(salt, hashed_password)

    # inserting the user record
    result = mysql.insertUser(fname, lname, email_id,
                              salt, hashed_password, q1, q2, profile, google_id)
    if result > 0:
        user_id = mysql.cur.fetchall()
        mysql.closeCursor()
        response = {
            "user_id": user_id,
            "first_name": fname,
            "last_name": lname,
            "email_id": email_id,
        }
        return maketoken.encode_token(app, response, user_id)
    else:
        mysql.closeCursor()
        return jsonify({
            'message': 'There was some error, Try again!!'
        }), 401


# this will be normal user login
@app.route("/login", methods=['POST'])
def login():
    payload = request.get_json()
    # email_id = str(payload['emailId'])
    # password = str(payload['password'])
    email_id = payload['emailId']
    password = payload['password']

    # look for the account, if it exists or not
    mysql = database.Database()  # database class object
    result = mysql.getUser(email_id)
    if result > 0:
        user_details = mysql.cur.fetchall()
        mysql.closeCursor()
        # print(user_details[0])
        pwd = user_details[0]['Password'].encode('utf-8')

        hpwd = password.encode('utf-8')
        res = bcrypt.checkpw(hpwd, pwd)
        # check if the passwords match or not
        if res:
            response = {
                'user_id': user_details[0]['UserID'],
                'first_name': user_details[0]['FName'],
                'last_name': user_details[0]['LName'],
                'email_id': user_details[0]['EmailID'],
            }
            return maketoken.encode_token(app, response, user_details[0]['UserID'])
        return jsonify({'message': 'wrong password'}), 401
    return jsonify({'message': 'account not found'}), 403

# this is for the forgot password
@app.route("/forgot", methods=['POST'])
def forgot():
    data = request.get_json()
    email_id = data['emailId']
    maiden = data['maidenName']
    artist = data['artistName']

    # look for the account, if it exists or not
    mysql = database.Database()  # database class object
    result = mysql.getUser(email_id)
    if result > 0:
        user_details = mysql.cur.fetchall()
        mysql.closeCursor()
        q1 = user_details[0]['Q1']
        q2 = user_details[0]['Q2']
        
        # check if the user has answered the 2 security questions correctly
        if maiden == q1 and artist == q2:
            return jsonify({ 'message': 'success' }), 200
    return jsonify({
        'message': 'There was some error, Try again!!'
    }), 401

# this is for the forgot password
@app.route("/updatepass", methods=['POST'])
def updatepass():
    data = request.get_json()
    email_id = data['emailId']
    new_pass = str(data['newpass'])

    # look for the account, if it exists or not
    mysql = database.Database()  # database class object
    result = mysql.getUser(email_id)
    if result > 0:
        user_details = mysql.cur.fetchall()

        bytes = new_pass.encode('utf-8')
        salt = str(user_details[0]['Salt']).encode('utf-8')
        hashed_password = bcrypt.hashpw(bytes, salt)
        hashed_password = hashed_password.decode('utf-8')

        # query for updating the password for this emailID 
        mysql.updatePass(email_id, hashed_password)
        mysql.closeCursor()

        return jsonify({ 'message': 'success' }), 200
    return jsonify({
        'message': 'There was some error, Try again!!'
    }), 401

# this is the google login
@app.route('/googlelogin', methods=['POST'])
def googlelogin():
    login_data = request.json
    try:
        idinfo = id_token.verify_oauth2_token(
            login_data['credential'], Request(), creds['CLIENT_ID'])
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        # ID token is valid. Get the user's Google Account ID from the decoded token.
        google_id = idinfo['sub']
        name = idinfo['name']
        email_id = idinfo['email']
        picture = idinfo['picture']

        name = name.split()

        fname = name[0]
        lname = name[1]
        salt = password = q1 = q2 = "dummy"

        # look for the account, if it already exists
        mysql = database.Database()  # database class object
        result = mysql.getUser(email_id)

        if result > 0 and mysql.cur.fetchall()[0]['GoogleID'] == "dummy":
            mysql.updateUserAsGoogleUser(email_id, google_id)

        if result == 0:
            mysql.insertUser(fname, lname, email_id, salt,
                             password, q1, q2, picture, google_id)
        mysql.closeCursor()

        mysql = database.Database()  # database class object
        result = mysql.getUser(email_id)
        user_details = mysql.cur.fetchall()

        response = {
            'user_id': user_details[0]['UserID'],
            'first_name': user_details[0]['FName'],
            'last_name': user_details[0]['LName'],
            'profile_pic': user_details[0]['ProfilePic']
        }
        print("its working")
        return maketoken.encode_token(app, response, user_details[0]['UserID'])
        # print(user_id, fname, lname, email_id, picture)
    except ValueError:
        # Invalid token
        print("error")
        return jsonify({'message': 'There was some error'}), 401


if __name__ == '__main__':
    app.run()
