import pymysql
import random
import yaml

# importing the credentials file
creds = yaml.safe_load(open('credentials.yaml'))

class Database:

    # setting up the database connection
    def __init__(self):
        host = creds['DB_HOST'],
        user = creds['DB_USER'],
        password = creds['DB_PASSWORD'],
        db = creds['DB_DATABASE'],

        # create the database connection and cursor
        self.con = pymysql.connect(
            host=host[0], user=user[0], password=password[0], db=db[0], cursorclass=pymysql.cursors.DictCursor)
        
        self.cur = self.con.cursor()

    # fetching the user details from the database
    def getUser(self, email_id):
        result = self.cur.execute(
            "SELECT * FROM User where EmailID = %s", (email_id))
        return result
    
    # fetching the user profile details from the database
    def getuProfile(self, user_id):
        result = self.cur.execute(
            "SELECT FName, LName, EmailID, ProfilePic, Contact, Street, City, State, Country, Zip FROM User where UserID = %s", (user_id))
        return result

    # adding the user details in the database
    def insertUser(self, fname, lname, email_id, salt, password, q1, q2, profile, google_id, contact, street, city, state, country, zip):
        self.cur.execute("INSERT INTO User (FName, LName, EmailID, Salt, Password, Q1, Q2, ProfilePic, GoogleID, Contact, Street, City, State, Country, Zip) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                         (fname, lname, email_id, salt, password, q1, q2, profile, google_id, contact, street, city, state, country, zip))
        self.con.commit()
        result = self.cur.execute(
            "SELECT UserID FROM User WHERE FName = %s AND LName = %s and EmailID = %s", (fname, lname, email_id))
        return result
    
       # updating the user details in the database
    def updateUser(self, userid, contact, street, city, state, country, zip):
        result = self.cur.execute("UPDATE User SET Contact = %s, Street = %s, City = %s, State = %s, Country = %s, Zip = %s WHERE UserID = %s", (contact, street, city, state, country, zip, userid))
        self.con.commit()
        return result
    
    # adding the product details in the database
    def insertProduct(self, user_id, pname, pdesc, pprice, pcategory, pimgurl, sname, scontact, sstreet, scity, sstate, scountry, szip, slat, slong):
        self.cur.execute("INSERT INTO Product (Name, Description, Price, Category, ImageURL, SIName, SIContact, SIStreet, SICity, SIState, SICountry, SIZip, SILat, SILon) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                         (pname, pdesc, pprice, pcategory, pimgurl, sname, scontact, sstreet, scity, sstate, scountry, szip, slat, slong))
        self.con.commit()
        res = self.cur.execute(
            "SELECT ProductID FROM Product WHERE Name = %s AND Category = %s AND ImageURL = %s AND SIName = %s AND SIZip = %s", (pname, pcategory, pimgurl, sname, szip))
        res_det = self.cur.fetchall()
        prod_id = res_det[0]['ProductID']
        method = "1"    # Method 1 = Product Posted by the User
        self.cur.execute("INSERT INTO user_product (UserID, ProductID, Method) VALUES(%s, %s, %s)", (user_id, prod_id, method))
        self.con.commit()
        return prod_id
    
    # fetching product details [universal - limited to admin view, pending for approval]
    def getallProducts(self):
        result = self.cur.execute("SELECT * FROM Product")
        return result
    
    # fetching product reviews
    def getProductReviews(self, product_id):
        result = self.cur.execute("SELECT * FROM review WHERE ProductID = %s", (product_id))
        return result
    
    # fetching product ratings
    def getProductRatings(self, product_id):
        result = self.cur.execute("SELECT AVG(Rating) AS AverageRatings FROM review WHERE ProductID = %s", (product_id))
        return result
    
    # inserting product reviews
    def insertProductReviews(self, user_id, rating, comment, product_id):
        result = self.cur.execute("INSERT INTO review (UserID, Rating, Comment, ProductID) VALUES (%s, %s, %s, %s)", (user_id, rating, comment, product_id))
        self.con.commit()
        return result
    
    # fetching products posted or purchased by the user [Posted = 1  |  Purchased = 2]
    def getUserProducts(self, user_id, method):
        result = self.cur.execute("SELECT product.* FROM product, user_product WHERE user_product.UserID = %s AND product.ProductID = user_product.ProductID AND user_product.method = %s", (user_id, method))
        return result
    
    # fetching single product details
    def getProduct(self, pid):
        result = self.cur.execute("SELECT * FROM Product WHERE ProductID = %s ", (pid))
        return result
    
    # fetching product details [user view - approved products]
    def getApprovedProduct(self):
        result = self.cur.execute("SELECT * FROM Product WHERE Status = %s ", (2))
        return result
    
    # fetching product details [admin view - rejected products]
    def getRejectedProduct(self):
        result = self.cur.execute("SELECT * FROM Product WHERE Status = %s ", (3))
        return result
    
    #   STATUS  =>  Pending = 1   |   Approved = 2    |   Rejected = 3
    
    # updating the product details
    def updateProducts(self, pid, pstatus):
        result = self.cur.execute("UPDATE Product SET Status = %s WHERE ProductID = %s", (pstatus, pid))
        self.con.commit()
        return result
    
    # get seller id of particular product
    def getSellerIdOfProduct(self, productid):
        result = self.cur.execute("SELECT UserID from user_product WHERE ProductID = %s", (productid))
        self.con.commit()
        return result

    # updating the password
    def updatePass(self, email, pwd):
        result = self.cur.execute("UPDATE User SET Password = %s WHERE EmailID = %s", (pwd, email))
        self.con.commit()
        return result

    # fetching google user details from the database
    def getGoogleUser(self, email_id, google_id):
        result = self.cur.execute( "SELECT * FROM User where EmailID = %s AND GoogleID = %s", (email_id, google_id))
        return result

    # adding google user in the database
    def updateUserAsGoogleUser(self, email_id, google_id):
        result = self.cur.execute( "UPDATE User SET GoogleID = %s WHERE EmailID = %s", (google_id, email_id))
        self.con.commit()
        return result

    # after each query executed, we close the cursor and the connection by calling this function
    def closeCursor(self):
        self.cur.close()
        self.con.close()
