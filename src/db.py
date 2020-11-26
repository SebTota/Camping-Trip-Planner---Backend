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


def get_username_by_email(email) -> dict:
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    sql = "SELECT Users_Username FROM Tbl_Users WHERE Users_Email = %s"
    cursor.execute(sql, (email,))

    res = cursor.fetchall()
    cursor.close()
    my_db.close()

    if len(res) == 0:
        return {"found": False, "username": ""}
    else:
        return {"found": True, "username": res[0][0]}


def get_pass_by_email(email) -> dict:
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


def get_profile_by_email(email) -> dict:
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    sql = "SELECT Users_First_Name, Users_Last_Name, Users_Username FROM Tbl_Users WHERE Users_Email = %s"
    cursor.execute(sql, (email,))

    res = cursor.fetchall()
    cursor.close()
    my_db.close()

    if len(res) == 0:
        return {"found": False, "profile": ""}
    else:
        return {"found": True, "profile": {
            "first_name": res[0][0].strip().title(),
            "last_name": res[0][1].strip().title(),
            "full_name": res[0][0].strip().title() + " " + res[0][1].strip().title(),
            "user_name": res[0][2]
        }}
      
      
def add_group_request(from_user_email, to_user_email, group_uuid):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    request_uuid = str(uuid.uuid4())
    sql = "INSERT INTO Tbl_Group_Requests (Request_User_To, Request_User_From, Request_Group_id, Request_Uuid) " \
          "SELECT " \
          "(SELECT _id FROM Tbl_Users WHERE Users_Email = %s) AS TO_USER, " \
          "(SELECT _id FROM Tbl_Users WHERE Users_Email = %s) AS FROM_USER, " \
          "(SELECT _id FROM Tbl_Groups WHERE Groups_Uuid = %s) AS GROUP_UUID, " \
          "%s " \
          "WHERE " \
          "(SELECT COUNT(1) FROM Tbl_Users " \
          "INNER JOIN Tbl_Group_Users ON Tbl_Group_Users.User_Id = Tbl_Users._id " \
          "INNER JOIN Tbl_Groups ON Tbl_Group_Users.Group_Id = Tbl_Groups._id " \
          "WHERE Tbl_Users.Users_Email = %s AND Tbl_Groups.Groups_Uuid = %s) = 0 " \
          "AND (SELECT COUNT(1) FROM Tbl_Users " \
          "INNER JOIN Tbl_Group_Requests ON Tbl_Group_Requests.Request_User_To = Tbl_Users._id " \
          "INNER JOIN Tbl_Groups ON Tbl_Group_Requests.Request_Group_id = Tbl_Groups._id " \
          "WHERE Tbl_Users.Users_Email = %s " \
          "AND Tbl_Groups.Groups_Uuid = %s) = 0"

    cursor.execute(sql, (to_user_email, from_user_email, group_uuid, request_uuid,
                         to_user_email, group_uuid, to_user_email, group_uuid))
    print(cursor.statement)
    my_db.commit()
    cursor.close()
    my_db.close()
    
    
def get_group_requests(user_email):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    sql = "SELECT Users_First_Name, Users_Last_Name, Request_Uuid, Group_Name FROM Tbl_Users INNER JOIN " \
          "(SELECT Tbl_Groups.Groups_Uuid, Tbl_Groups.Group_Name, Tbl_Group_Requests.Request_User_From, Tbl_Group_Requests.Request_Uuid FROM Tbl_Users " \
          "INNER JOIN Tbl_Group_Requests ON Tbl_Users._id = Tbl_Group_Requests.Request_User_To " \
          "INNER JOIN Tbl_Groups ON Tbl_Group_Requests.Request_Group_id = Tbl_Groups._id " \
          "WHERE Tbl_Users.Users_Email = %s) " \
          "AS res on res.Request_User_From = Tbl_Users._id"

    cursor.execute(sql, (user_email,))

    res = cursor.fetchall()
    cursor.close()
    my_db.close()

    if len(res) == 0:
        return []
    else:
        d1 = list(dict())
        for i in range(len(res)):
            d1.append({
                "invite-from": res[i][0].strip().title() + " " + res[i][1].strip().title(),
                'group-name': res[i][3],
                'request-uuid': res[i][2]
            })
        return d1


def remove_group_invite_request(request_uuid):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    sql = "DELETE FROM Tbl_Group_Requests WHERE Request_Uuid = %s"
    cursor.execute(sql, (request_uuid,))
    my_db.commit()
    cursor.close()
    my_db.close()
    
    
def accept_group_invite_request(email, request_uuid):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    sql = "INSERT INTO Tbl_Group_Users(Group_Id, User_Id) " \
          "SELECT " \
          "(SELECT Request_Group_id FROM Tbl_Group_Requests WHERE Request_Uuid = %s), " \
          "(SELECT _id FROM Tbl_Users WHERE Users_Email = %s)"
    cursor.execute(sql, (request_uuid, email))
    my_db.commit()
    cursor.close()
    my_db.close()
    remove_group_invite_request(request_uuid)


def create_list(name, group_id):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    list_uuid = str(uuid.uuid4())
    cmd = "INSERT INTO Tbl_Lists (Lists_Name, Group_id, Lists_Uuid) " \
          "VALUES (%s,%s, %s)"
    vls = (name, group_id, list_uuid)
    cursor.execute(cmd, vls)
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
    query = "SELECT Lists_Uuid, Lists_Name FROM Tbl_Lists " \
            "INNER JOIN Tbl_Groups ON Tbl_Lists.Group_id = Tbl_Groups._id " \
            "WHERE Tbl_Groups.Groups_Uuid = %s"
    cursor.execute(query, (group_id,))
    res = cursor.fetchall()
    my_db.commit()
    cursor.close()
    my_db.close()

    if len(res) == 0:
        return []
    else:
        d1 = list(dict())
        for i in range(len(res)):
            d1.append({
                "list-name": res[i][0],
                'list-id': res[i][1],
            })
        return d1

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


def delete_user_from_group(user_id, group_uuid):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()

    cmd = "DELETE a FROM Tbl_Group_Users a " \
          "INNER JOIN Tbl_Groups b on a.Group_Id = b._id " \
          "INNER JOIN Tbl_Users u on a.User_Id = u._id " \
          "WHERE Users_Email = %s AND Groups_Uuid = %s "

    vls = (user_id, group_uuid,)
    cursor.execute(cmd, vls)

    my_db.commit()
    cursor.close()
    my_db.close()


def get_group_uuid_by_user(email):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()

    cmd = "SELECT Group_Name, Groups_Uuid FROM Tbl_Groups " \
          "INNER JOIN Tbl_Group_Users " \
          "ON Tbl_Group_Users.Group_Id = Tbl_Groups._id " \
          "INNER JOIN Tbl_Users " \
          "ON Tbl_Group_Users.User_Id = Tbl_Users._id " \
          "WHERE Users_Email = %s"

    vls = (email, )
    cursor.execute(cmd, vls)

    res = cursor.fetchall()

    cursor.close()
    my_db.close()

    if len(res) == 0:
        return []
    else:
        ret_list = list(dict())
        for i in range(len(res)):
            ret_list.append({
                "group-name": res[i][0],
                'group-uuid': res[i][1],
            })
        return ret_list


if __name__ == '__main__':
    accept_group_invite_request('tui43030@temple.edu', 'd34df504-b123-490e-a2ef-c956a4384f3d')