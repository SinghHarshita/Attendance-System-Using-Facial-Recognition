import mysql.connector
import ast
import numpy as np
import json
import MainPage
#static dictionaries here : 

#db connectivity here : 
db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="attendance_system"
)

cursor=db.cursor()

dept_id = {
    1 : "dept1",
    2 : "dept2",
    3 : "dept3",
    4 : "dept4",
}

role_id = {
    0 : "student",
    1 : "subject teacher",
    2 : "class teacher",
}

months = {
    1 : "Jan",
    2 : "Feb",
    3 : "March",
    4 : "April",
    5 : "May",
    6 : "June",
    7 : "July",
    8 : "Aug",
    9 : "Sept",
    10 : "Oct",
    11 : "Nov",
    12 : "Dec",
}

#query functions here : 
def login(request,master):
    """
    Login functionality and role wise page calling done here 
    """
    sql = "SELECT * FROM user WHERE email_id = %(email_id)s AND password = %(password)s"
    
    cursor.execute(sql,request)
    answer = cursor.fetchone()
    
    #print(answer)
    
    if answer != None:
        if answer[2] != None:

            data = {
                "u_id"     : answer[0],
                "details"  : answer[1],
                "email_id" : answer[5],
                "password" : answer[5],
                "class"    : answer[3],
                "role_id"  : answer[2],
            }
            #print(data["details"][0])
            if data['role_id'] == 0:
                import Student
                Student.Student(master, data)
            elif data['role_id'] == 1:
                import Teacher
                Teacher.Teacher(master, data)
            elif data['role_id'] == 2:
                import ClassTeacher
                ClassTeacher.ClassTeacher(master,data)
            elif data["role_id"] == 3:
                import AdminPage
                AdminPage.Admin(master, data)
        else:
            import MainPage
            import tkinter.messagebox as tm
            tm.showerror("Role Unassigned", "Ask the admin to assign a role")
            MainPage.MainPage(master).login_page(1)
    else:
        import MainPage
        import tkinter.messagebox as tm
        tm.showerror("Invalid User", "Incorrect email or password!")
        MainPage.MainPage(master).login_page(1)
        
def store(request,master):
    """
    Registeration of new students 
    call face recognintion on student registeration,capture images and then store
    else store data directly
    """
    request["details"] = str(request["details"])
    sql = "INSERT INTO user(details, class, role_id, email_id, password) VALUES(%(details)s, %(class)s, %(role_id)s, %(email_id)s, %(password)s)"
    cursor.execute(sql,request)
    db.commit()

    # Get the u_id of the new user

    query1 = "SELECT u_id FROM user ORDER BY u_id DESC LIMIT 0,1"
    cursor.execute(query1)
    id = cursor.fetchone()
    user_id = int(id[0])
    print(id[0])

    if request["role_id"] == 0:
        folder = str(id[0])
        import test
        img_path = str(test.capture(folder))

        # Save the directory path in image column`
        #img_path="F:\\SUMEDH\\python\\mini-project\\images\\"+str(user_id)
        image_path_update = {
        "image" : img_path,
        "id"    : user_id,
        }

        query2 = "UPDATE user SET image =%(image)s WHERE u_id =%(id)s"
        print(query2,img_path,str(user_id))
        cursor.execute(query2, image_path_update)
        db.commit()
        
        # Training dataset
    
        import faces_train as ft
        ft.func()
        MainPage.MainPage(master).login_page(1)

def get_student_details(selected_class, flag):
    sql = "SELECT * FROM user WHERE role_id = 0 AND class LIKE %(class)s"
    arg = {
        "class" : selected_class
    }
    cursor.execute(sql, arg)
    result = cursor.fetchall()
    data = dict()

    if flag == 0:
        for x in result:
            details = ast.literal_eval(x[1])
            data[details["roll_no"]] = {
                "name"       : details["name"],
                "email_id"   : x[5],
                "attendance" : 0,
            }
    else:
        for x in result:
            details = ast.literal_eval(x[1])
            data[details["roll_no"]] = {
                "name" : details["name"],
                "email_id" : x[5],
                "gender" : details["gender"],
                "u_id" : x[0],
                "class" : x[3],
            }
    #print(data)
    return data

def get_class_attendance(id):
    """ Fetches the attendance of the class """
    #print(id)
    args = {"class" : "%" +id + "%"}

    sql = "SELECT * FROM subject_allotment WHERE role LIKE %(class)s"

    cursor.execute(sql, args)
    result_subjects = cursor.fetchall()

    subjects = list()
    attendance = dict()

    if result_subjects == None or len(result_subjects) == 0:
        return -1, -1
    for s in result_subjects:
        subjects = (ast.literal_eval(s[2])[id])
        for sub in ast.literal_eval(s[2])[id]:
            attendance[sub] = get_attendance(s[0], id, sub, 1)
    students = get_student_details(id, 0)
    #print(attendance)
    
    return attendance, students

def get_subject(id):
    """ Fetches the subjects taught and the attendance of the students """
    request = {
        "t_id" : id
    }
    sql = "SELECT * FROM subject_allotment WHERE t_id = %(t_id)s"
    cursor.execute(sql,request)
    result = cursor.fetchone()
    
    #print(result)

    data = dict()

    if result != None:
        data["u_id"]        = result[1]
        data["sub_alot_id"] = result[0]
        if result[2] == None:
            data["subjects"] = None
        else :
            
            data["subjects"] = ast.literal_eval(result[2])
           
    #print(data)
    return data

def cal_attendance(data, students, flag):
    #print(students)

    attendance = 0
    month_vise_attendance = dict()
    month_date = dict()
    dates = list(data.keys())
    count = 0
    n = len(list(students.keys()))

    if flag == 0:
        """ Calculating month-vise attendance """
        
        # Grouping dates month-vise
        for date in dates:
            if months[date.month] in month_date:
                month_date[months[date.month]].append(date)
            else:
                month_date[months[date.month]] = [date]
        #print(month_date)
        
        # Calculating attendance
        m = list(month_date.keys())

        for x in m:
            """ The month """
            att = [0] * n
            count = 0
            for date in month_date[x]:
                """ Gets the date """
                slots = list(data[date].keys())
                for s in slots : 
                    """ Slot on a particular day """
                    count += 1
                    for roll_no in data[date][s][0]:
                        """ Get the roll number present """
                        att[roll_no - 1] += 1
            if count >= 1:
                att = list(np.array(att)/count * 100)
            month_vise_attendance[x] = att
            pass
        #print(month_vise_attendance)
        return month_vise_attendance
    
    for date in dates: 
        slots = list(data[date].keys())
        for s in slots:
            count += 1
            for roll_no in data[date][s][0]:
                students[str(roll_no)]["attendance"] += 1

    if flag == 1:
        _attendance = list()
        r = list(students.keys())
        for x in r:
            if count >= 1:
                students[x]["attendance"] = float(students[x]["attendance"]/count * 100)
            _attendance.append(students[x]["attendance"])
            
        return _attendance
    print(students)
    return students

def get_attendance(sub_alot_id, selected_class, subject, flag):
    """
        Gets the attendance for particular teacher
    """
    request = {
        "sub_alot_id" : sub_alot_id,
        #"attendance"  : "%"+selected_class+"*"+subject+"%"
    }
    
    sql = "SELECT * FROM attendance WHERE sub_alot_id = %(sub_alot_id)s"
    cursor.execute(sql, request)

    result = cursor.fetchall()
    if result == None or len(result) == 0:
        if flag == 1:
            return -1
        else:
            return -1, -1
    
    
    data, i = dict(), 0
    for x in result:
        e = ast.literal_eval(x[2])
        a = list(e.keys())
        att = dict()
        for _ in a:
            #e[_] = ast.literal_eval(e[a])
            if e[_][0] == selected_class and e[_][1] == subject:
                att[_] = e[_][2:]

        data[x[1]] = att
        i += 1
    #print(data)

    students = get_student_details(selected_class, 0)

    attendance = cal_attendance(data, students, flag)
    #print(data, students)
    if flag == 1:
        return attendance
    return attendance, students

def get_att_records(id):
    """ Getting records for the edit page """

    subjects = get_subject(id)
    print(subjects)
    
    sql = "SELECT * FROM attendance WHERE sub_alot_id = %(sub_alot_id)s"
    sub = {
        "sub_alot_id" : subjects["sub_alot_id"]
    }
    cursor.execute(sql, sub)
    result = cursor.fetchall()
    
    for x in result:
        subjects[x[1]] = ast.literal_eval(x[2])

    return subjects

def get_teacher_details():
    """ Gets details of all the teachers """
    sql = "SELECT * FROM user WHERE role_id = 1 or role_id = 2"
    cursor.execute(sql)

    result = cursor.fetchall()
    
    if result == None or len(result) == 0:
        return -1

    t_det = list()

    for x in result:
        data = dict()
        data["u_id"] = x[0]
        data["details"] = ast.literal_eval(x[1])
        data["role"] = x[2]
        data["email_id"] = x[5]
        data["class"] = x[3]
        t_det.append(data)
    return t_det

def fetch_attendance(uid,class_):
    #pass
    x=fetch_subjects(class_)
    k=0
    w=0
    response=dict()
    for i in range(len(x)):
        sub_id=x[i]["subject_allotment_id"]
        sql="Select date,attendance from attendance where sub_alot_id= {}".format(sub_id)
        cursor.execute(sql,sub_id)
        result=cursor.fetchall()
        #rint(result)
        for r in result:
            #print(type(r))
            d=ast.literal_eval(r[1])
            l=list(d.values())
            #print(l)
            for j in l:
                if uid in j[2]:
                    response[w]={
                            "time" : [time for time in d.keys()],
                            "theory/pracs" : j[1],
                            "date" : r[0]
                        }
                    w=w+1
    return response
    #pass

def fetch_subjects(class_):
    sql="Select * from subject_allotment"
    cursor.execute(sql)
    result=cursor.fetchall()
    response=dict()
    i=0 
    for x in result :
        d=ast.literal_eval(x[2])
        for k in d.keys():
            if k==class_:
                response[i]={
                    "subject_allotment_id":x[0],
                    "t_id" : x[1],
                    "role" : d[k]
                }
                i=i+1
    #print("\r\r\r")
    #print(response)    
    return response

def fetch_tname(id):
    cursor.execute("Select details from user where u_id = {}".format(id))
    res=cursor.fetchone()
    res=ast.literal_eval(res[0])
    return res["name"]
    pass

def calc_attendance(subject,id,class_,uid):
    cursor.execute("Select attendance from attendance where sub_alot_id = {}".format(id))
    res=cursor.fetchall()
    #print(res)
    k=0
    a=0
    for x in res:
        r=ast.literal_eval(x[0])
        for v in r.values():
            if v[0]==class_ and v[1]==subject:
                k=k+1
                if uid in v[2]:
                    a=a+1
    return (a/k)*100

def edit_att_list(data,date):
    #print(date)
    """ Getting Attendance of Particular Date """
    sql1 = "SELECT * FROM attendance WHERE sub_alot_id = " + str(data['sub_alot_id']) + " and date = '" + str(date['yy']) + '-' + str(date['mm']) + '-' + str(date['dd']) + "'"
    #print(sql1)
    cursor.execute(sql1)
    answer = cursor.fetchone()
    #print(answer[2],"hiii\n\n")
    if answer:
        return eval(answer[2])
    else:
        return -1

def get_uids(class1):
    """ Getting List of Records of Student of Particular Class """
    sql1 = "SELECT * FROM user WHERE class = '" + str(class1) + "' and role_id = '0'"
    print(sql1,"hii\n\n")
    cursor.execute(sql1)
    answer = cursor.fetchall()
    print(answer)
    return answer
    
def get_sub_alot_id(t_id,class1,sub):
    sql1 = "SELECT * FROM subject_allotment where t_id = " + str(t_id) + " and role LIKE '%" + str(class1) + "%" + str(sub) + "%'"
    #print(sql1,"\n\n")
    cursor.execute(sql1)
    ans = cursor.fetchone()
    #print(ans[0])
    return ans[0]

def update_att_record(sub_alot_id,date,class1,sub,uids):
    sql1 = "SELECT * FROM attendance WHERE sub_alot_id = " + str(sub_alot_id) + " and date = '" + str(date) + "'"
    print(sql1)
    cursor.execute(sql1)
    ans = cursor.fetchone()
    det = eval(ans[2])
    cl_vals = list(det.values()) #contains all values of dictionary
    cl_keys = list(det.keys())
    for i in range(len(cl_vals)):
        if cl_vals[i][0] == str(class1) and cl_vals[i][1] == str(sub):
            cl_vals[i][2] = uids
            det[cl_keys[i]] = cl_vals[i]
            break
    det_json = json.dumps(det)
    print(ans)
    sql2 = "UPDATE attendance set attendance = '" + det_json + "' WHERE sub_alot_id = " + str(sub_alot_id) + " and date = '" + str(date) + "'"
    print(sql2)
    cursor.execute(sql2)
    db.commit()


def list_lec(data):
    sql1 = "SELECT * FROM subject_allotment WHERE t_id = " + str(data['u_id']) 
    cursor.execute(sql1)
    answer = cursor.fetchall()
    tp = eval(answer[0][2])
    print(answer)
    
    det = tp.items()
    #print(det,data["u_id"])
    return det
    
def mark_att(data,dict1):
    sql1 = "SELECT * FROM attendance where sub_alot_id = '" + str(dict1['sub_alot_id']) + "' and date = '" + dict1['date'] + "'"
    cursor.execute(sql1)
    data = cursor.fetchone()
    if data is None:
        """ if data do not exist in database for that day """
        temp_dict = dict()
        list1 = []
        list1.append(dict1['class1'])
        list1.append(dict1['subject'])
        list1.append(dict1['uids_rolls'])
        temp_dict[dict1['time']] = list1

        #convert dictionary into json to load into database
        json_ent = json.dumps(temp_dict)

        sql2 = "INSERT into attendance(sub_alot_id,date,attendance) values (%s,%s,%s)"
        val = (str(dict1['sub_alot_id']),dict1['date'],json_ent)
        cursor.execute(sql2,val)
        db.commit()
    else:
        """ if data already exist in database for that particular day """
        det = eval(data[2])
        list1 = []
        list1.append(dict1['class1'])
        list1.append(dict1['subject'])
        list1.append(dict1['uids_rolls'])
        det[dict1['time']] = list1
        json_ent = json.dumps(det)
        sql2 = "Update attendance set attendance = %s where sub_alot_id = %s and date = %s"
        print("\n" + sql2 + "\n")
        val = (json_ent,dict1['sub_alot_id'],dict1['date'])
        cursor.execute(sql2,val)
        db.commit()
    
def get_class_uid(cl):
    sql = "SELECT u_id FROM user where class = %s and role_id = %s"
    cursor.execute(sql,(cl,0))
    obj = cursor.fetchall()
    temp = []
    for i in obj:
        temp.append(i[0])
    #print(obj[0][0],obj[1][0])
    return temp

def delete_user(id):
    """ Delete User """
    sql = "DELETE FROM user WHERE id = %s"
    cursor.execute(sql,id)
    db.commit()
    
