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
    mysql = database.Database()
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
        return jsonify({ 'message': 'There was some error, Try again!!' }), 401

# this will be normal user login
@app.route("/login", methods=['POST'])
def login():
    payload = request.get_json()
    # email_id = str(payload['emailId'])
    # password = str(payload['password'])
    email_id = payload['emailId']
    password = payload['password']

    # look for the account, if it exists or not
    mysql = database.Database()
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

    mysql = database.Database()
    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]
    # user token validation
    if maketoken.decode_token(app, user_id, token):
        result = mysql.getUser(email_id)
        # look for the account, if it exists or not
        if result > 0:
            user_details = mysql.cur.fetchall()
            mysql.closeCursor()
            q1 = user_details[0]['Q1']
            q2 = user_details[0]['Q2']
            
            # check if the user has answered the 2 security questions correctly
            if maiden == q1 and artist == q2:
                return jsonify({ 'message': 'success' }), 200
        return jsonify({ 'message': 'There was some error, Try again!!' }), 401
    return jsonify({ 'message': 'Invalid Token' }), 401

# this is for updating the password
@app.route("/updatepass", methods=['POST'])
def updatepass():
    data = request.get_json()
    email_id = data['emailId']
    new_pass = str(data['newpass'])

    # look for the account, if it exists or not
    mysql = database.Database()
    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]
    # user token validation
    if maketoken.decode_token(app, user_id, token):
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
        return jsonify({ 'message': 'There was some error, Try again!!' }), 401
    return jsonify({ 'message': 'Invalid Token' }), 401

# this is for fetching user details
@app.route("/getuprofile", methods=['GET'])
def uprofile():
    data = request.get_json()
    email_id = data['emailId']

    # look for the account, if it exists or not
    mysql = database.Database()
    result = mysql.getuProfile(email_id)
    if result > 0:
        user_details = mysql.cur.fetchall()
        mysql.closeCursor()

        return jsonify(user_details), 200
    return jsonify({ 'message': 'There was some error, Try again!!' }), 401

# this is for inserting product details
@app.route("/insertproduct", methods=['POST'])
def insertproduct():
    mysql = database.Database()
    pdata = request.get_json()
    pname = pdata['name']
    pdesc = pdata['description']
    pprice = pdata['price']
    pcategory = pdata['category']
    pimgurl = pdata['imgurl']
    sname = pdata['sname']
    scontact = pdata['scontact']
    sstreet = pdata['sstreet']
    scity = pdata['scity']
    sstate = pdata['sstate']
    scountry = pdata['scountry']
    szip = pdata['szip']
    # print(pname, pdesc, pprice, pcategory, pimgurl, sname, scontact, sstreet, scity, sstate, scountry, szip)

    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]
    # user token validation
    if maketoken.decode_token(app, user_id, token):
        # look for the account, if it already exists
        pid = mysql.insertProduct(user_id, pname, pdesc, pprice, pcategory, pimgurl, sname, scontact, sstreet, scity, sstate, scountry, szip)
        if pid > 0:
            mysql.closeCursor()
            return jsonify({ 'message': 'product added successfully' }), 200
        else:
            return jsonify({ 'message': 'There was some error, Try again!!' }), 401
    return jsonify({ 'message': 'Invalid Token' }), 401

# this is for fetching the product details for admin panel
@app.route("/getallproducts", methods=['GET'])
def getallproducts():
    mysql = database.Database()
    result = mysql.getallProducts()
    if result > 0:
        product_details = mysql.cur.fetchall()
        mysql.closeCursor()
        return jsonify(product_details), 200
    else:
        return jsonify({ 'message': 'There was some error, Try again!!' }), 401
    
# this is for fetching all the approved product details for user view
@app.route("/getapprovedproducts", methods=['GET'])
def getapprovedproducts():
    mysql = database.Database()
    result = mysql.getApprovedProduct()
    if result > 0:
        product_details = mysql.cur.fetchall()
        mysql.closeCursor()
        return jsonify(product_details), 200
    else:
        return jsonify({ 'message': 'There are no approved products' }), 401
    
# this is for fetching all the rejected product details
@app.route("/getrejectedproducts", methods=['GET'])
def getrejectedproducts():
    mysql = database.Database()
    result = mysql.getRejectedProduct()
    if result > 0:
        product_details = mysql.cur.fetchall()
        mysql.closeCursor()
        return jsonify(product_details), 200
    else:
        return jsonify({ 'message': 'There are no rejected products' }), 401
    
# this is for fetching all products posted by the user [method = 1]
@app.route("/upposted", methods=['GET'])
def upposted():
    data = request.get_json()
    email_id = data['emailId']

    mysql = database.Database()
    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]
    # user token validation
    if maketoken.decode_token(app, user_id, token):
        result = mysql.getUser(email_id)
        # look for the account, if it exists or not
        if result > 0:
            res = mysql.getUserProducts(user_id, "1")
            if res > 0:
                user_details = mysql.cur.fetchall()
                mysql.closeCursor()
                return jsonify(user_details), 200
            return jsonify({'message': 'There are no posted products by user'}), 200
        return jsonify({ 'message': 'There was some error, Try again!!' }), 401
    return jsonify({ 'message': 'Invalid Token' }), 401

# this is for fetching all products purchased by the user [method = 2]
@app.route("/uppurchased", methods=['GET'])
def uppurchased():
    data = request.get_json()
    email_id = data['emailId']

    mysql = database.Database()
    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]
    # user token validation
    if maketoken.decode_token(app, user_id, token):
        result = mysql.getUser(email_id)
        # look for the account, if it exists or not
        if result > 0:
            res = mysql.getUserProducts(user_id, "2")
            if res > 0:
                user_details = mysql.cur.fetchall()
                mysql.closeCursor()
                return jsonify(user_details), 200
            return jsonify({'message': 'There are no purchased products by user'}), 200
        return jsonify({ 'message': 'There was some error, Try again!!' }), 401
    return jsonify({ 'message': 'Invalid Token' }), 401

@app.route("/dummy", methods=["GET"])
def dummy():
    temp = {"temp":"temp"}
    return maketoken.encode_token(app, temp, "2")
    

# this is for updating the product status (admin approval)
@app.route("/productstatus", methods=["PATCH"])
def productstatus():
    mysql = database.Database()
    pdata = request.get_json()
    pid = pdata['productid']
    pstatus = pdata['productstatus']
    result = mysql.updateProducts(pid, pstatus)
    if result > 0:
        mysql.closeCursor()
        return jsonify({ 'message': 'success' }), 200
    else:
        return jsonify({ 'message': 'There was some error, Try again!!' }), 401

# this is for google login
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
