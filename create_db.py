# This file is intended for initial setup of RIO's database
# pip install mysql-connector

import yaml
import mysql.connector

# secret credentials
creds = yaml.safe_load(open('credentials.yaml'))

mydb = mysql.connector.connect(
    host = creds['DB_HOST'],
    user = creds['DB_USER'],
    password = creds['DB_PASSWORD'],
)

my_cursor = mydb.cursor()

# STEP 1 -> Create a Database
my_cursor.execute("CREATE DATABASE RIO;")
my_cursor.execute("USE RIO;")

# Step 2 -> Creating the required Tables
my_cursor.execute("CREATE TABLE `User` ( `UserID` INT NOT NULL, `FName` VARCHAR(255) NOT NULL, `LName` VARCHAR(255) NOT NULL, `EmailID` VARCHAR(255) NOT NULL, `Salt` VARCHAR(255) NOT NULL, `Password` VARCHAR(255) NOT NULL, `Q1` VARCHAR(255) NOT NULL, `Q2` VARCHAR(255) NOT NULL, `Q3` VARCHAR(255) NOT NULL, PRIMARY KEY (`UserID`));")
my_cursor.execute("CREATE TABLE `Product` ( `ProductID` INT NOT NULL, `Name` VARCHAR(255) NOT NULL, `Description` VARCHAR(512) NOT NULL, `Price` DECIMAL NOT NULL, `Category` VARCHAR(255) NOT NULL, `Date` TIMESTAMP NOT NULL, `Rating` INT NOT NULL DEFAULT '0', `Status` INT NOT NULL DEFAULT '1', `ImageURL` VARCHAR(255) NOT NULL, `AdminRemark` VARCHAR(255), `SIName` VARCHAR(255) NOT NULL, `SIContact` VARCHAR(255) NOT NULL, `SIStreet` VARCHAR(255) NOT NULL, `SICity` VARCHAR(255) NOT NULL, `SIState` VARCHAR(255) NOT NULL, `SICountry` VARCHAR(255) NOT NULL, `SIZip` VARCHAR(255) NOT NULL, PRIMARY KEY (`ProductID`) );")
my_cursor.execute("CREATE TABLE `UserProduct` ( `UserID` VARCHAR(255) NOT NULL, `ProductID` VARCHAR(255) NOT NULL, PRIMARY KEY (`UserID`,`ProductID`) );")
my_cursor.execute("CREATE TABLE `Review` ( `UserID` INT NOT NULL, `Rating` INT NOT NULL, `Comment` VARCHAR(255) NOT NULL );")
my_cursor.execute("CREATE TABLE `Complaint` ( `ProductID` INT NOT NULL, `Description` VARCHAR(255) NOT NULL, `SUserID` INT NOT NULL, `Date` TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP );")

print("RIO Database Setup Completed")


'''
### Things to Know ###

[STATUS in Product Table] -
1 = Pending
2 = Approved
3 = Rejected

'''