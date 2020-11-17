import mysql.connector
import mysql.connector.pooling
import os
import uuid


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


def create_list(name, group_id):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    list_uuid = str(uuid.uuid4())
    cmd = "INSERT INTO Tbl_Lists (Lists_Name, Group_id, Lists_Uuid) " \
          "VALUES (%s,%s, %s)"

    vls = (name, group_id, list_uuid)
    cursor.execute(cmd, vls)
    print("test2")
    cmd2 = "SELECT LAST_INSERT_ID()"
    cursor.execute(cmd2)
    retVal = cursor.fetchall()
    my_db.commit()
    cursor.close()
    my_db.close()
    return retVal[0][0]


def get_list_by_id(list_id):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    query = "SELECT Lists_Name, Group_id FROM Tbl_Lists " \
            "WHERE _id = %s"
    cursor.execute(query, (list_id,))
    retVal = cursor.fetchall()
    my_db.commit()
    cursor.close()
    my_db.close()
    return retVal


def delete_list_by_id(list_id):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd1 = "DELETE FROM Tbl_Elements WHERE Elements_id = %s"
    cmd2 = "DELETE FROM Tbl_Lists WHERE _id = %s"
    cursor.execute(cmd1, (list_id,))
    cursor.execute(cmd2, (list_id,))
    my_db.commit()
    cursor.close()
    my_db.close()


def get_items_in_list(list_id):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    query = "SELECT _id, Elements_Name, Elements_Value, Elements_User_id, Elements_Quantity FROM Tbl_Elements " \
            "WHERE Elements_id = %s"
    cursor.execute(query, (list_id,))
    retVal = cursor.fetchall()
    my_db.commit()
    cursor.close()
    my_db.close()
    return retVal


# returns array of list_ids that are in the group
def get_lists_in_group(group_id):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    query = "SELECT _id FROM Tbl_Lists " \
            "WHERE Group_id = %s"
    cursor.execute(query, (group_id,))
    retVal = cursor.fetchall()
    my_db.commit()
    cursor.close()
    my_db.close()
    return [id[0] for id in retVal]


def add_item_to_list(list_id, name, quantity=1, user_id=0, unit_cost=0):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    item_uuid = str(uuid.uuid4())
    cmd = "INSERT INTO Tbl_Elements (Elements_id, Elements_Name, Elements_Value, " \
          "Elements_User_id, Elements_Quantity, Elements_Uuid) VALUES (%s,%s,%s,%s,%s,%s)"

    vls = (list_id, name, unit_cost, user_id, quantity, item_uuid)
    cursor.execute(cmd, vls)
    my_db.commit()
    cursor.close()
    my_db.close()


def change_cost_of_item(item_id, new_cost):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd = "UPDATE Tbl_Elements " \
          "SET Elements_Value = %s " \
          "WHERE _id = %s"
    cursor.execute(cmd, (new_cost, item_id))
    my_db.commit()
    cursor.close()
    my_db.close()


def change_name_of_item(item_id, new_name):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd = "UPDATE Tbl_Elements " \
          "SET Elements_Name = %s " \
          "WHERE _id = %s"
    cursor.execute(cmd, (new_name, item_id))
    my_db.commit()
    cursor.close()
    my_db.close()


def claim_item(item_id, user_id):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd = "UPDATE Tbl_Elements " \
          "SET Elements_User_id = %s " \
          "WHERE _id = %s"
    cursor.execute(cmd, (user_id, item_id))
    my_db.commit()
    cursor.close()
    my_db.close()


def unclaim_item(item_id):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    cmd = "UPDATE Tbl_Elements " \
          "SET Elements_User_id = 0 " \
          "WHERE _id = %s"
    cursor.execute(cmd, (item_id,))
    my_db.commit()
    cursor.close()
    my_db.close()


if __name__ == '__main__':
    if(True):
        id = create_list("test", 0)
        print(id)
        print("test")
        print("test4")
        add_item_to_list(id, "test")

        claim_item(4, 3)
        unclaim_item(4)
        change_cost_of_item(4, 5)
        print(get_lists_in_group(1))

        add_item_to_list(11, "additional item")
        print(get_items_in_list(11))
        delete_list_by_id(11)

        print(get_list_by_id(10))
