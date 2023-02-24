from flask import Flask, request
from flask_cors import CORS, cross_origin
from google.oauth2 import id_token
from google.auth.transport.requests import Request
import yaml
import mysql.connector

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

# creating the database cursor
my_cursor = mydb.cursor()

# this will be part of the user registration process
@app.route("/register")
def register():
    my_cursor.execute("SELECT * from user")
    result = my_cursor.fetchall()
    for db in result:
        print(db)
    return result 

# this will be part of normal user login
@app.route("/login")
def login():
    my_cursor.execute("SELECT * from user")
    result = my_cursor.fetchall()
    for db in result:
        print(db)
    return result

# this will be part of google login
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
    app.run(debug=True)