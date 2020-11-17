import mysql.connector
import mysql.connector.pooling
import os


cnxpool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=3,
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database="camping-trip-planner"
)


def sign_up_db(first_name, last_name, email, password):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd = "INSERT INTO Tbl_Users (Users_Email, Users_Verified, Users_Password, " \
          "Users_First_Name, Users_Last_Name, Users_Username) VALUES " \
          "(%s,%s,%s,%s,%s,%s)"

    vls = (email, True, password, first_name, last_name, email)
    cursor.execute(cmd, vls)
    my_db.commit()
    cursor.close()
    my_db.close()


def check_if_user_exists_by_email(email):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    sql = "SELECT COUNT(1) FROM Tbl_Users WHERE Users_Email = %s"
    cursor.execute(sql, (email,))

    res = cursor.fetchall()
    cursor.close()
    my_db.close()

    if res[0][0] == 0:
        print("Email does not exist")
        return False
    else:
        print("Email exists")
        return True


def check_if_username_exists(username):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    sql = "SELECT COUNT(1) FROM Tbl_Users WHERE Users_Username = %s"
    cursor.execute(sql, (username,))

    res = cursor.fetchall()
    cursor.close()
    my_db.close()

    if res[0][0] == 0:
        print("Username does not exist")
        return False
    else:
        print("Username exists")
        return True


def get_password(email):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    sql = "SELECT Users_Password FROM Tbl_Users WHERE Users_Email = %s"
    cursor.execute(sql, (email,))

    res = cursor.fetchall()
    cursor.close()
    my_db.close()

    if len(res) == 0:
        return {"found": False, "pass": ""}
    else:
        return {"found": True, "pass": res[0][0]}


def add_element(element):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd = "INSERT INTO Tbl_Elements (Elements_Name) VALUES " \
          "(%s)"

    vls = (element,)
    cursor.execute(cmd, vls)
    my_db.commit()
    cursor.close()
    my_db.close()


def delete_element(element):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd = "DELETE FROM Tbl_Elements WHERE " \
          "Elements_Name= (%s)"

    vls = (element,)
    cursor.execute(cmd, vls)
    my_db.commit()
    cursor.close()
    my_db.close()


def edit_element(new, element):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd = "UPDATE Tbl_Elements SET Elements_Name= (%s) WHERE " \
          "Elements_Name= (%s)"

    vls = (new, element)
    cursor.execute(cmd, vls)
    my_db.commit()
    cursor.close()
    my_db.close()


def get_user_id_by_username(user_name):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd = "SELECT _id FROM Tbl_Users WHERE Users_Username = %s"

    vls = (user_name,)
    cursor.execute(cmd, vls)

    res = cursor.fetchall()
    cursor.close()
    my_db.close()

    if len(res) == 0:
        return {"found": False, "user_id": "does not exist"}
    else:
        return {"found": True, "user_id": res[0][0]}


def delete_user_from_group(user_name):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()

    user_id = get_user_id_by_username(user_name)

    cmd = "DELETE FROM Tbl_Group_Users WHERE User_Id= (%s)"

    vls = (user_id,)
    cursor.execute(cmd, str(vls))

    cursor.close()
    my_db.close()


def get_group_by_user(user_name):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()

    user_id = get_user_id_by_username(user_name)

    cmd = "SELECT Group_Id FROM Tbl_Group_Users WHERE User_Id = %s"

    vls = (user_id,)
    cursor.execute(cmd, vls)

    res = cursor.fetchall()
    cursor.close()
    my_db.close()

    if len(res) == 0:
        return {"found": False, "group_id": "user doesn't belong to a group"}
    else:
        return {"found": True, "user_id": res[0][0]}


# def get_list_by_group_id(group_id):


if __name__ == '__main__':
    email = "tui43030@temple.edu"
    print(get_group_by_user(email))

