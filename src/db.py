import mysql.connector
import os

my_db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database="camping-trip-planner"
)


def sign_up_db(first_name, last_name, email, password):
    cursor = my_db.cursor()
    cmd = "INSERT INTO Tbl_Users (Users_Email, Users_Verified, Users_Password, " \
          "Users_First_Name, Users_Last_Name, Users_Username) VALUES " \
          "(%s,%s,%s,%s,%s,%s)"

    vls = (email, True, password, first_name, last_name, email)
    cursor.execute(cmd, vls)
    my_db.commit()
    cursor.close()


def check_if_user_exists_by_email(email):
    cursor = my_db.cursor()
    cursor.execute("SELECT Users_Email FROM Tbl_Users")
    emails = cursor.fetchall()

    for row in emails:
        if email in row:
            print("Email exists")
            return True
        else:
            print("Email does not exist")
            return False


def check_if_username_exists(username):
    cursor = my_db.cursor()
    cursor.execute("SELECT Users_Username FROM Tbl_Users")
    usernames = cursor.fetchall()

    for row in usernames:
        if username in row:
            print("Username exists")
            return True
        else:
            print("Username does not exist")
            return False



if __name__ == '__main__':
    check_if_username_exists("guy")
