import mysql.connector
import os

mydb = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database="camping-trip-planner"
)

def signUpDb(first_name,last_name,email,password):

    cursor = mydb.cursor()
    cmd = "INSERT INTO Tbl_Users (Users_Email,Users_Verified,Users_Password," \
      "Users_First_Name,Users_Last_Name,Users_Username) VALUES " \
      "(%s,%s,%s,%s,%s,%s)"

    vls = (email, True, password, first_name, last_name, email)
    cursor.execute(cmd, vls)
    mydb.commit()