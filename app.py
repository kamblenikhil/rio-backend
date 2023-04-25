from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from google.oauth2 import id_token
from google.auth.transport.requests import Request
import yaml
import maketoken
import database
import bcrypt
import googlemaps
import os
import datetime
import requests
import json

app = Flask(__name__)
CORS(app)

# secret credentials
# creds = yaml.safe_load(open('credentials.yaml'))
# app.config['SECRET_KEY'] = creds['APP_SECRET']
app.config['SECRET_KEY'] = os.environ.get('APP_SECRET')

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
    profile = google_id = contact = street = city = state = country = zip = "dummy"
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
    result = mysql.insertUser(fname, lname, email_id, salt, hashed_password,
                              q1, q2, profile, google_id, contact, street, city, state, country, zip)
    if result > 0:
        user_id = mysql.cur.fetchall()
        mysql.closeCursor()
        response = {
            "user_id": user_id[0]['UserID'],
            "first_name": fname,
            "last_name": lname,
            "email_id": email_id,
        }
        return maketoken.encode_token(app, response, user_id)
    else:
        mysql.closeCursor()
        return jsonify({'message': 'There was some error, Try again!!'}), 401

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
    # user token validation
    result = mysql.getUser(email_id)
    # look for the account, if it exists or not
    if result > 0:
        user_details = mysql.cur.fetchall()
        mysql.closeCursor()
        q1 = user_details[0]['Q1']
        q2 = user_details[0]['Q2']

        # check if the user has answered the 2 security questions correctly
        if maiden == q1 and artist == q2:
            return jsonify({'message': 'success'}), 200
    return jsonify({'message': 'There was some error, Try again!!'}), 401

# this is for updating the password


@app.route("/updatepass", methods=['POST'])
def updatepass():
    data = request.get_json()
    email_id = data['emailId']
    new_pass = str(data['newpass'])

    # look for the account, if it exists or not
    mysql = database.Database()
    # user token validation
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

        return jsonify({'message': 'success'}), 200
    return jsonify({'message': 'There was some error, Try again!!'}), 401

# this is for fetching user details


@app.route("/getuprofile", methods=['GET'])
def userprofile():
    user_id = request.args.get('id')

    # look for the account, if it exists or not
    mysql = database.Database()
    result = mysql.getuProfile(user_id)
    if result > 0:
        user_details = mysql.cur.fetchall()
        mysql.closeCursor()

        return jsonify(user_details), 200
    return jsonify({'message': 'There was some error, Try again!!'}), 401

# this is for updating the profile details


@app.route("/updateprofile", methods=['POST'])
def updateprofile():
    data = request.get_json()
    user_id = request.args.get('id')
    contact = data['contact']
    street = data['street']
    city = data['city']
    state = data['state']
    country = data['country']
    zip = data['zip']

    # look for the account, if it exists or not
    mysql = database.Database()
    result = mysql.updateUser(user_id, contact, street,
                              city, state, country, zip)
    if result > 0:
        user_details = mysql.cur.fetchall()
        mysql.closeCursor()
        return jsonify(user_details), 200
    else:
        return jsonify({'message': 'There was some error, Try again!!'}), 401


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

    address = sstreet + scity + sstate + scountry + szip
    # gmaps_key = googlemaps.Client(key=creds['GOOGLE_MAPS'])
    gmaps_key = googlemaps.Client( key = os.environ.get('GOOGLE_MAPS'))
    g = gmaps_key.geocode(address)
    slat = g[0]["geometry"]["location"]["lat"]
    slong = g[0]["geometry"]["location"]["lng"]
    # print(pname, pdesc, pprice, pcategory, pimgurl, sname, scontact, sstreet, scity, sstate, scountry, szip)

    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]

    token = token[1:-1]
    # user token validation
    if maketoken.decode_token(app, int(user_id), token):
        # look for the account, if it already exists
        pid = mysql.insertProduct(user_id, pname, pdesc, pprice, pcategory,
                                  pimgurl, sname, scontact, sstreet, scity, sstate, scountry, szip, slat, slong)
        if pid > 0:
            mysql.closeCursor()
            return jsonify({'message': 'product added successfully'}), 200
        else:
            return jsonify({'message': 'There was some error, Try again!!'}), 401
    return jsonify({'message': 'Invalid Token'}), 401

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
        return jsonify({'message': 'There was some error, Try again!!'}), 401

# this is for fetching all the approved product details for user view


@app.route("/getapprovedproducts", methods=['GET'])
def getapprovedproducts():
    mysql = database.Database()
    result = mysql.getApprovedProduct()
    if result > 0:
        product_details = mysql.cur.fetchall()
        response = []
        for prods in product_details:
            img = prods['ImageURL']
            img_list = img.split(",")
            imgurl = img_list[0]
            res = {
                'pid': prods['ProductID'],
                'pname': prods['Name'],
                'rating': prods['Rating'],
                'img': imgurl,
                'price': prods['Price'],
                'category': prods['Category'],
                'desc': prods['Description'],
                'SICity': prods['SICity'],
                "SIContact": prods["SIContact"],
                "SICountry": prods["SICountry"],
                "SIName": prods["SIName"],
                "SIState": prods["SIState"],
                "SIStreet": prods["SIStreet"],
                "SIZip": prods["SIZip"],
            }
            response.append(res)

        mysql.closeCursor()
        return jsonify(response), 200
    else:
        return jsonify({'message': 'There are no approved products'}), 401

# this is for fetching all the rejected product details


@app.route("/getrejectedproducts", methods=['GET'])
def getrejectedproducts():
    mysql = database.Database()
    result = mysql.getRejectedProduct()
    if result > 0:
        product_details = mysql.cur.fetchall()
        response = []
        for prods in product_details:
            img = prods['ImageURL']
            img_list = img.split(",")
            imgurl = img_list[0]
            res = {
                'pid': prods['ProductID'],
                'pname': prods['Name'],
                'rating': prods['Rating'],
                'img': imgurl,
                'price': prods['Price'],
                'category': prods['Category'],
                'desc': prods['Description'],
                'SICity': prods['SICity'],
                "SIContact": prods["SIContact"],
                "SICountry": prods["SICountry"],
                "SIName": prods["SIName"],
                "SIState": prods["SIState"],
                "SIStreet": prods["SIStreet"],
                "SIZip": prods["SIZip"],

            }
            response.append(res)
        mysql.closeCursor()
        return jsonify(product_details), 200
    else:
        return jsonify({'message': 'There are no rejected products'}), 401

# this is for fetching a single product details for user view


@app.route("/getproduct", methods=['GET'])
def getproduct():
    product_id = request.args.get('productid')
    mysql = database.Database()
    result = mysql.getProduct(product_id)
    if result > 0:
        product_details = mysql.cur.fetchall()
        response = []
        for prods in product_details:
            img = prods['ImageURL']
            img_list = img.split(",")
            res = {
                'pid': prods['ProductID'],
                'pname': prods['Name'],
                'rating': prods['Rating'],
                'img': img_list,
                'price': prods['Price'],
                'category': prods['Category'],
                'desc': prods['Description'],
                'SICity': prods['SICity'],
                "SIContact": prods["SIContact"],
                "SICountry": prods["SICountry"],
                "SIName": prods["SIName"],
                "SIState": prods["SIState"],
                "SIStreet": prods["SIStreet"],
                "SIZip": prods["SIZip"],
                "SILat": prods["SILat"],
                "SILon": prods["SILon"],
                "pStatus": prods["Status"]
            }
            response.append(res)
        mysql.closeCursor()
        return jsonify(res), 200
    else:
        return jsonify({'message': 'This product does not exist'}), 401

# this is for fetching all the pending products
@app.route("/getpendingproducts", methods=['GET'])
def getpendingproducts():
    mysql = database.Database()
    result = mysql.getPendingProduct()
    if result > 0:
        product_details = mysql.cur.fetchall()
        response = []
        for prods in product_details:
            img = prods['ImageURL']
            img_list = img.split(",")
            imgurl = img_list[0]
            res = {
                'pid': prods['ProductID'],
                'pname': prods['Name'],
                'rating': prods['Rating'],
                'img': imgurl,
                'price': prods['Price'],
                'category': prods['Category'],
                'desc': prods['Description'],
                'SICity': prods['SICity'],
                "SIContact": prods["SIContact"],
                "SICountry": prods["SICountry"],
                "SIName": prods["SIName"],
                "SIState": prods["SIState"],
                "SIStreet": prods["SIStreet"],
                "SIZip": prods["SIZip"],

            }
            response.append(res)
        mysql.closeCursor()
        return jsonify(response), 200
    else:
        return jsonify({'message': 'There are no pending products'}), 401


# this is for fetching all the rented products
@app.route("/getrentedproducts", methods=['GET'])
def getrentedproducts():
    mysql = database.Database()
    result = mysql.getRentedProduct()
    if result > 0:
        product_details = mysql.cur.fetchall()
        response = []
        for prods in product_details:
            img = prods['ImageURL']
            img_list = img.split(",")
            imgurl = img_list[0]
            res = {
                'pid': prods['ProductID'],
                'pname': prods['Name'],
                'rating': prods['Rating'],
                'img': imgurl,
                'price': prods['Price'],
                'category': prods['Category'],
                'desc': prods['Description'],
                'SICity': prods['SICity'],
                "SIContact": prods["SIContact"],
                "SICountry": prods["SICountry"],
                "SIName": prods["SIName"],
                "SIState": prods["SIState"],
                "SIStreet": prods["SIStreet"],
                "SIZip": prods["SIZip"],

            }
            response.append(res)
        mysql.closeCursor()
        return jsonify(response), 200
    else:
        return jsonify({'message': 'There are no rented products'}), 401
    
# this is for fetching all products posted by the user [method = 1]


@app.route("/upposted", methods=['POST'])
def upposted():
    data = request.get_json()
    email_id = data['emailId']
    mysql = database.Database()
    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]
    token = token[1:-1]
    # user token validation
    if maketoken.decode_token(app, int(user_id), token):
        result = mysql.getUser(email_id)
        # look for the account, if it exists or not
        if result > 0:
            res = mysql.getUserProducts(int(user_id), 1)
            if res > 0:
                product_details = mysql.cur.fetchall()
                response = []

                for prods in product_details:
                    img = prods['ImageURL']
                    img_list = img.split(",")
                    imgurl = img_list[0]
                    res = {
                        'pid': prods['ProductID'],
                        'pname': prods['Name'],
                        'rating': prods['Rating'],
                        'img': imgurl,
                        'price': prods['Price'],
                        'category': prods['Category'],
                        'desc': prods['Description'],
                        'SICity': prods['SICity'],
                        "SIContact": prods["SIContact"],
                        "SICountry": prods["SICountry"],
                        "SIName": prods["SIName"],
                        "SIState": prods["SIState"],
                        "SIStreet": prods["SIStreet"],
                        "SIZip": prods["SIZip"],
                    }
                    response.append(res)
                mysql.closeCursor()
                return jsonify(response), 200
            return jsonify({'message': 'There are no posted products by user'}), 401
        return jsonify({'message': 'There was some error, Try again!!'}), 401
    return jsonify({'message': 'Hello Invalid Token'}), 401

# this is for fetching all products purchased by the user [method = 2]


@app.route("/uppurchased", methods=['POST'])
def uppurchased():
    data = request.get_json()
    email_id = data['emailId']

    mysql = database.Database()
    user_id = request.args.get('id')
    token = request.headers['Authorization'].split(" ")[1]
    token = token[1:-1]
    # user token validation
    if maketoken.decode_token(app, int(user_id), token):
        result = mysql.getUser(email_id)
        # look for the account, if it exists or not
        if result > 0:
            res = mysql.getUserProducts(int(user_id), 2)
            if res > 0:
                product_details = mysql.cur.fetchall()
                response = []

                for prods in product_details:
                    img = prods['ImageURL']
                    img_list = img.split(",")
                    imgurl = img_list[0]
                    res = {
                        'pid': prods['ProductID'],
                        'pname': prods['Name'],
                        'rating': prods['Rating'],
                        'img': imgurl,
                        'price': prods['Price'],
                        'category': prods['Category'],
                        'desc': prods['Description'],
                        'SICity': prods['SICity'],
                        "SIContact": prods["SIContact"],
                        "SICountry": prods["SICountry"],
                        "SIName": prods["SIName"],
                        "SIState": prods["SIState"],
                        "SIStreet": prods["SIStreet"],
                        "SIZip": prods["SIZip"],
                    }
                    response.append(res)
                mysql.closeCursor()
                return jsonify(response), 200
            return jsonify({'message': 'There are no purchased products by user'}), 401
        return jsonify({'message': 'There was some error, Try again!!'}), 401
    return jsonify({'message': 'Invalid Token'}), 401

# rent a product


@app.route("/rentaproduct", methods=['POST'])
def rentaproduct():
    mysql = database.Database()
    data = request.get_json()
    user_id = request.args.get('id')
    product_id = data['productId']
    token = request.headers['Authorization'].split(" ")[1]
    token = token[1:-1]
    # user token validation
    if maketoken.decode_token(app, int(user_id), token):
        result = mysql.rentaproduct(user_id, product_id)
        if result > 0:
            res = mysql.cur.fetchall()
        emailId = res[0]['EmailID']
        print(emailId)
        mysql.closeCursor()
        # email confirmation receipt to the sender
        # url = creds['RAPID_API_URL']
        url = os.environ.get('RAPID_API_URL')

        payload = {"personalizations": [{"to": [{"email": emailId}], "subject": "RIO - Payment Confirmation Receipt"}], "from": {"email": "no-reply@rio.com"},
                   "content": [{"type": "text/plain", "value": "Thank you for renting the Product from RIO. Your payment was received successfully."}]}

        # headers = {"content-type": "application/json",
                #    "X-RapidAPI-Key": creds['X-RapidAPI-Key'], "X-RapidAPI-Host": creds['X-RapidAPI-Host']}
        headers = {"content-type": "application/json","X-RapidAPI-Key": os.environ.get('X-RapidAPI-Key'),"X-RapidAPI-Host": os.environ.get('X-RapidAPI-Host')}

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 202:
            return jsonify({'message': 'Product Rented Successfully, Payment Email Sent'}), 200
        return jsonify({'message': 'Product Rented Successfully, Payment Email Not Sent.'}), 200
    return jsonify({'message': 'Invalid Token'}), 401

# this is for fetching product reviews


@app.route("/getprodreviews", methods=['GET'])
def getprodreviews():
    mysql = database.Database()
    product_id = request.args.get('productid')
    result = mysql.getProductReviews(product_id)
    if result > 0:
        pdetails = mysql.cur.fetchall()
        mysql.closeCursor()
        return jsonify(pdetails), 200
    else:
        return jsonify({'message': 'There are no reviews for this product'}), 200

# this is for fetching if the user has rented the given product or not


@app.route("/getrentedproductstatus", methods=['GET'])
def getrentedproductstatus():
    mysql = database.Database()
    user_id = request.args.get('id')
    product_id = request.args.get('product_id')
    result = mysql.getRentedProductStatus(user_id, product_id)
    if result > 0:
        pdetails = mysql.cur.fetchall()
        mysql.closeCursor()
        return jsonify(pdetails), 200
    else:
        return jsonify({'message': 'There are no reviews for this product'}), 200

# this is for inserting product review


@app.route("/insertprodreviews", methods=['POST'])
def insertprodreviews():
    mysql = database.Database()
    pdata = request.get_json()
    user_id = request.args.get('id')
    rating = pdata['rating']
    comment = pdata['comment']
    product_id = pdata['productid']
    result = mysql.insertProductReviews(user_id, rating, comment, product_id)
    if result > 0:
        mysql.closeCursor()
        return jsonify({'message': 'added product rating successfully'}), 200
    return jsonify({'message': 'There was some error, Try again!!'}), 401

# this is for filing a complaint


@app.route("/fileacomplaint", methods=['POST'])
def fileacomplaint():
    mysql = database.Database()
    pdata = request.get_json()
    user_id = request.args.get('id')
    product_id = request.args.get('product_id')
    description = pdata['description']
    today = datetime.datetime.now()
    date = today.strftime('%Y-%m-%d %H:%M:%S')
    result = mysql.fileacomplaint(product_id, description, user_id, date)
    if result > 0:
        mysql.closeCursor()
        return jsonify({'message': 'you complaint was successfully posted'}), 200
    return jsonify({'message': 'There was some error, Try again!!'}), 401

# this is for getting complaint's


@app.route("/getcomplaints", methods=['GET'])
def getcomplaints():
    mysql = database.Database()
    result = mysql.getcomplaints()
    if result > 0:
        complaints = mysql.cur.fetchall()
        mysql.closeCursor()
        return jsonify(complaints), 200
    return jsonify({'message': 'There was some error, Try again!!'}), 401

# this is for testing purpose only


@app.route("/dummy", methods=["POST"])
def dummy():
    # temp = {"temp": "temp"}
    # return maketoken.encode_token(app, temp, "2")
    return "Hello! This website works..."

# this is for updating the product status (admin approval)


@app.route("/productstatus", methods=['PUT'])
def productstatus():
    mysql = database.Database()
    pdata = request.get_json()
    pid = pdata['productid']
    pstatus = pdata['productstatus']
    result = mysql.updateProducts(pid, pstatus)
    if result > 0:
        mysql.closeCursor()
        return jsonify({'message': 'success'}), 200
    else:
        return jsonify({'message': 'There was some error, Try again!!'}), 401

# this is for getting seller id of a product


@app.route("/getsellerid", methods=['POST'])
def getsellerid():
    mysql = database.Database()
    data = request.get_json()
    product_id = data['productid']
    result = mysql.getSellerIdOfProduct(product_id)
    if len(result) > 0:
        # pdetails = mysql.cur.fetchall()
        mysql.closeCursor()
        return jsonify(result), 200
    else:
        return jsonify({'message': 'No Seller Found'}), 401

# this is for product recommendation


@app.route("/getproductrecommendation", methods=['POST'])
def getproductrecommendation():
    mysql = database.Database()
    data = request.get_json()
    category = data['category']
    productid = data['pid']
    result = mysql.getProductRecommendation(category, productid)
    if result > 0:
        product_details = mysql.cur.fetchall()
        response = []
        for prods in product_details:
            res = {
                'pid': prods['ProductID'],
                'pname': prods['Name'],
                'rating': prods['Rating'],
                'img': prods['ImageURL'],
                'price': prods['Price'],
                'category': prods['Category'],
                'desc': prods['Description'],
                'SICity': prods['SICity'],
                "SIContact": prods["SIContact"],
                "SICountry": prods["SICountry"],
                "SIName": prods["SIName"],
                "SIState": prods["SIState"],
                "SIStreet": prods["SIStreet"],
                "SIZip": prods["SIZip"],
            }
            response.append(res)
        mysql.closeCursor()
        return jsonify(response), 200
    else:
        return jsonify({'message': 'No Seller Found'}), 401

# this is for getting renter details of a product


@app.route("/getrenterdetails", methods=['POST'])
def getrenterdetails():
    mysql = database.Database()
    data = request.get_json()
    product_id = data['productid']
    result = mysql.getRenterDetails(product_id)
    if result > 0:
        pdetails = mysql.cur.fetchall()
        mysql.closeCursor()
        return jsonify(pdetails), 200
    else:
        return jsonify({'message': 'No Seller Found'}), 401

# this is for google login


@app.route('/googlelogin', methods=['POST'])
def googlelogin():
    login_data = request.json
    try:
        # print(login_data['credential'],login_data['clientId'] == creds['CLIENT_ID'])
        idinfo = id_token.verify_oauth2_token(
            # login_data['credential'], Request(), creds['CLIENT_ID'])
            login_data['credential'], Request(), os.environ.get('CLIENT_ID'))
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
        salt = password = q1 = q2 = contact = street = city = state = country = zip = "dummy"

        # look for the account, if it already exists
        mysql = database.Database()  # database class object
        result = mysql.getUser(email_id)

        if result > 0 and mysql.cur.fetchall()[0]['GoogleID'] == "dummy":
            mysql.updateUserAsGoogleUser(email_id, google_id)

        if result == 0:
            mysql.insertUser(fname, lname, email_id, salt, password, q1, q2,
                             picture, google_id, contact, street, city, state, country, zip)
        mysql.closeCursor()

        mysql = database.Database()  # database class object
        result = mysql.getUser(email_id)
        user_details = mysql.cur.fetchall()

        response = {
            'user_id': user_details[0]['UserID'],
            'first_name': user_details[0]['FName'],
            'last_name': user_details[0]['LName'],
            'profile_pic': user_details[0]['ProfilePic'],
            'email_id': user_details[0]['EmailID']
        }

        return maketoken.encode_token(app, response, user_details[0]['UserID'])
        # print(user_id, fname, lname, email_id, picture)
    except ValueError:
        # Invalid token
        return jsonify({'message': 'There was some error'}), 401


if __name__ == '__main__':
    app.run(debug=True)
