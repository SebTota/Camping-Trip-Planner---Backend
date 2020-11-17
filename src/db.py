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
            "first_name": res[0][0],
            "last_name": res[0][1],
            "full_name": res[0][0].strip().title() + " " + res[0][1].strip().title(),
            "user_name": res[0][2]
        }}


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


def add_group_request(from_user_email, to_user_email, group_uuid):
    my_db = cnxpool.get_connection()
    cursor = my_db.cursor()
    request_uuid = str(uuid.uuid4())
    sql = "INSERT INTO Tbl_Group_Requests (Request_User_To, Request_User_From, Request_Group_id, Request_Uuid) " \
          "SELECT " \
          "(SELECT _id FROM Tbl_Users WHERE Users_Email = %s) AS TO_USER, " \
          "(SELECT _id FROM Tbl_Users WHERE Users_Email = %s) AS FROM_USER, " \
          "(SELECT _id FROM Tbl_Groups WHERE Groups_Uuid = %s) AS GROUP_UUID, " \
          "%s"

    cursor.execute(sql, (to_user_email, from_user_email, group_uuid, request_uuid))
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


if __name__ == '__main__':
    add_group_request('seb1@gmail.com', 'tui43030@temple.edu', '2194d399-b955-49d3-a242-4eebbc4f8d23')
    add_group_request('seb1tota@gmail.com', 'tui43030@temple.edu', 'ba36f7ca-e8d2-42f9-9b65-ec9dc9fc51f2')
    #print(get_group_requests('tui43030@temple.edu'))
