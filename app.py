from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from google.oauth2 import id_token
from google.auth.transport.requests import Request
import yaml
import mysql.connector
import bcrypt

app = Flask(__name__)
CORS(app)

# secret credentials
creds = yaml.safe_load(open('credentials.yaml'))

# creating the SQL Connection
mydb = mysql.connector.connect(
    host = creds['DB_HOST'],
    user = creds['DB_USER'],
    passwd = creds['DB_PASSWORD'],
    database = creds['DB_DATABASE'],
)

# this is the part of user registration (signup)
@app.route("/signup", methods=['POST'])
def signup():
    payload = request.get_json()
    fname = payload['firstName']
    lname = payload['lastName']
    email_id = payload['emailId']
    password = str(payload['password'])
    q1 = payload['maiden']
    q2 = payload['artist']
    q3 = "dummy"

    # print(fname, lname, email_id, password, password, q1, q2, q3)

    # look for the account, if it already exists
    my_cursor = mydb.cursor()
    query1 = "SELECT count(*) AS count FROM user WHERE EmailID = \'" + email_id + "\';"
    my_cursor.execute(query1)
    records1 = my_cursor.fetchall()

    if records1[0][0] == 1:
        return jsonify({'message': 'account already exists'}), 401

    # generating the salt and hashing the password with salt
    bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(bytes, salt)

    # decoding the binary format to store them in the database
    salt = salt.decode('utf-8')
    hashed_password = hashed_password.decode('utf-8')

    # print(salt, hashed_password)
    
    # counting the users in user table
    my_cursor = mydb.cursor()
    my_cursor.execute("SELECT count(*) AS count FROM user;")
    records2 = my_cursor.fetchall()
    user_no = records2[0][0] + 1

    # inserting the user record
    my_cursor = mydb.cursor()
    query2 = "INSERT INTO user VALUES("+"\'"+str(user_no)+"\',"+"\'"+str(fname)+"\',"+"\'"+str(lname)+"\',"+"\'"+str(email_id)+"\',"+"\'"+str(salt)+"\',"+"\'"+str(hashed_password)+"\',"+"\'"+str(q1)+"\',"+"\'"+str(q2)+"\',"+"\'"+str(q3)+"\');"
    print(query2)
    my_cursor.execute(query2)
    mydb.commit()
    my_cursor.close()

    return jsonify({'message': 'success'}), 200 

# this will be normal user login
@app.route("/login", methods=['POST'])
def login():
    payload = request.get_json()
    email_id = str(payload['emailId'])
    password = str(payload['password'])

    # look for the account, if it exists or not
    my_cursor = mydb.cursor()
    query1 = "SELECT EmailID, Password FROM user WHERE EmailID = \'" + email_id + "\';"
    my_cursor.execute(query1)
    records1 = my_cursor.fetchall()

    print(records1)

    if len(records1) != 0:
        # checking if the account exists or not
        if str(records1[0][0]) == email_id:
            pwd = records1[0][1].encode('utf-8')
            hpwd = password.encode('utf-8')
            res = bcrypt.checkpw(hpwd, pwd)
            # check if the passwords match or not
            if res:
                return jsonify({'message': 'success'}), 200 
            else:
                return jsonify({'message': 'wrong password'}), 401
        else:
            return jsonify({'message': 'account not found'}), 401
    else:
        return jsonify({'message': 'account not found'}), 401
          

# this is the google login
@app.route('/googlelogin', methods=['POST'])
def googlelogin():
    login_data = request.json
    try:
        idinfo = id_token.verify_oauth2_token(login_data['credential'], Request(), creds['CLIENT_ID'])
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        name = idinfo['name']
        email = idinfo['email']
        picture = idinfo['picture']

        print(userid, name, email, picture)
    except ValueError:
        # Invalid token
        pass

    return 'success'

if __name__ == '__main__':
    app.run()