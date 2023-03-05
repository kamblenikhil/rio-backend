
import pymysql
import random
import yaml

# db = yaml.safe_load(open('db.yaml'))
# host = db["host"]
# user = db["user"]
# password = db["password"]
# db = db["db"]

creds = yaml.safe_load(open('credentials.yaml'))


class Database:

    def __init__(self):

        host = creds['DB_HOST'],
        user = creds['DB_USER'],
        password = creds['DB_PASSWORD'],
        db = creds['DB_DATABASE'],
        # print(host[0], user[0], password[0], db[0])
        self.con = pymysql.connect(
            host=host[0], user=user[0], password=password[0], db=db[0], cursorclass=pymysql.cursors.DictCursor)
        self.cur = self.con.cursor()

    def getUser(self, email_id):
        result = self.cur.execute(
            "SELECT * FROM User where EmailID = %s", (email_id))
        return result

    def insertUser(self, fname, lname, email_id, salt, password, q1, q2, profile, google_id):
        self.cur.execute("INSERT INTO User (FName, LName, EmailID, Salt, Password, Q1, Q2, ProfilePic, GoogleID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                         (fname, lname, email_id, salt, password, q1, q2, profile, google_id))
        self.con.commit()
        result = self.cur.execute(
            "SELECT UserID FROM User WHERE FName = %s AND LName = %s and EmailID = %s", (fname, lname, email_id))
        return result

    def getGoogleUser(self, email_id, google_id):
        result = self.cur.execute(
            "SELECT * FROM User where EmailID = %s AND GoogleID = %s", (email_id, google_id))
        return result

    def updateUserAsGoogleUser(self, email_id, google_id):
        result = self.cur.execute(
            "UPDATE User SET GoogleID = %s WHERE EmailID = %s", (google_id, email_id))
        self.con.commit()
        return result

    def closeCursor(self):
        self.cur.close()
        self.con.close()
