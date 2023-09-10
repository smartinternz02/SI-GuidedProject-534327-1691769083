from flask import Flask, render_template, request, session
import ibm_db
import ibm_boto3
from ibm_botocore.client import Config, ClientError
import os
import re
import random
import string
import datetime
import requests

app = Flask(__name__)

conn = ibm_db.connect("DATABASE=bludb; HOSTNAME=b70af05b-76e4-4bca-a1f5-23dbb4c6a74e.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud; PORT=32716; UID=yms88774;PASSWORD=u9eRWpksHM33mXZd; SECURITY=SSL;SSLServerCertificate = DigiCertGlobalRootCA.crt", "", "")
url = "https://rapidprod-sendgrid-v1.p.rapidapi.com/mail/send"
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/index")
def index2():
    return render_template("index.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/studentprofile")
def sprofile():
    return render_template("student.html")

@app.route("/adminprofile")
def aprofile():
    return render_template("adminprofile.html")

@app.route("/facultyprofile")
def fprofile():
    return render_template("facultyprofile.html")


@app.route("/login", methods=['POST','GET'])
def loginentered():
    global Userid
    global Username
    msg = ''
    if request.method == "POST":
        email = str(request.form['email'])
        print(email)
        password = request.form["password"]
        sql = "SELECT * FROM REGISTER WHERE EMAIL=? AND PASSWORD=?"  # from db2 sql table
        stmt = ibm_db.prepare(conn, sql)
        # this username & password is should be same as db-2 details & order also
        ibm_db.bind_param(stmt, 1, email)
        ibm_db.bind_param(stmt, 2, password)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account: 
            session['Loggedin'] = True
            session['id'] = account['EMAIL']
            Userid = account['EMAIL']
            session['email'] = account['EMAIL']
            Username = account['USERNAME']
            Name = account['NAME']
            msg = "logged in successfully !"
            sql = "SELECT ROLE FROM register where email = ?"
            stmt = ibm_db.prepare(conn, sql)
            ibm_db.bind_param(stmt, 1, email)
            ibm_db.execute(stmt)
            r = ibm_db.fetch_assoc(stmt)
            print(r)
            if r['ROLE'] == 1:
                print("STUDENT")
                return render_template("student.html", msg=msg, user=email, name = Name, role= "STUDENT", username=Username, email = email)
            elif r['ROLE'] == 2:
                print("FACULTY")
                return render_template("faculty.html", msg=msg, user=email, name = Name, role= "FACULTY", username=Username, email = email)
            else:
                return render_template('admin.html', msg=msg, user=email, name = Name, role= "ADMIN", username=Username, email = email)
        else:
            msg = "Incorrect Email/password"

        return render_template("login.html", msg=msg)
    else:
        return render_template("login.html")


@app.route("/studentsubmit", methods=['POST','GET'])
def sassignment():
    u = Username.strip()
    subtime = []
    ma = []
    sql = "SELECT SUBMITTIME, MARKS from SUBMIT WHERE STUDENTNAME = ? "
    stmt = ibm_db.prepare(conn, sql)            
    ibm_db.bind_param(stmt, 1, u)           
    ibm_db.execute(stmt)
    st = ibm_db.fetch_tuple(stmt)
    while st !=False:
        subtime.append(st[0])
        ma.append(st[1])
        st = ibm_db.fetch_tuple(stmt)
    print(subtime)
    print(ma)
    if request.method=="POST":
       for x in range (1,5):
        x = str(x)
        y = str("file"+x)
        print(type(y))
        f=request.files[ y ]
        print(f)
        print(f.filename)
        
        
        
        if f.filename != '':
            
            basepath=os.path.dirname(__file__) #getting the current path i.e where app.py is present
            #print("current path",basepath)
            filepath=os.path.join(basepath,'uploads',u+x+".pdf") #from anywhere in the system we can give image but we want that image later  to process so we are saving it to uploads folder for reusing
            #print("upload folder is",filepath)
            f.save(filepath)
            # connecting with cloud object storage
            
            COS_ENDPOINT = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"
            COS_API_KEY_ID = "MyX-mvA9jC3Nd6IZdsLRIg8EMLZXW4T6pjMx50nKfxCt"
            COS_INSTANCE_CRN = "crn:v1:bluemix:public:cloud-object-storage:global:a/ce2c0eb98c754e8287f7b5f407af741b:8502b471-4589-4c6c-af13-3ef1bb7f87c4::"
            cos = ibm_boto3.resource("s3",ibm_api_key_id=COS_API_KEY_ID,ibm_service_instance_id=COS_INSTANCE_CRN, config=Config(signature_version="oauth"),endpoint_url=COS_ENDPOINT)
            cos.meta.client.upload_file(Filename= filepath,Bucket='studentforprashant',Key= u+x+".pdf")
            msg = "Uploading Successful"
            ts = datetime.datetime.now()
            t = ts.strftime("%Y-%m-%d %H:%M:%S")
            sql1 = "SELECT * FROM SUBMIT WHERE STUDENTNAME = ? AND ASSIGNMENTNUM = ?"
            stmt = ibm_db.prepare(conn, sql1)
            ibm_db.bind_param(stmt, 1, u)
            ibm_db.bind_param(stmt, 2, x)
            ibm_db.execute(stmt)
            acc = ibm_db.fetch_assoc(stmt)
            print(acc)
            if acc == False:
                sql = "INSERT into SUBMIT (STUDENTNAME, ASSIGNMENTNUM, SUBMITTIME) values (?,?,?)"
                stmt = ibm_db.prepare(conn, sql)
                ibm_db.bind_param(stmt, 1, u) 
                ibm_db.bind_param(stmt, 2, x)
                ibm_db.bind_param(stmt, 3, t)
                ibm_db.execute(stmt)
            else:
                sql = "UPDATE SUBMIT SET SUBMITTIME = ? WHERE STUDENTNAME = ? and ASSIGNMENTNUM = ?"
                stmt = ibm_db.prepare(conn, sql)
                ibm_db.bind_param(stmt, 1, t)
                ibm_db.bind_param(stmt, 2, u)
                ibm_db.bind_param(stmt, 3, x)
                ibm_db.execute(stmt)
            
            
            return render_template("studentsubmit.html", msg=msg, datetime=subtime, Marks=ma)
    return render_template("studentsubmit.html", datetime=subtime, Marks=ma)

@app.route("/facultymarks")
def facultymarks():
    data=[]
    sql = "SELECT USERNAME from REGISTER WHERE ROLE=1"
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.execute(stmt)
    name = ibm_db.fetch_tuple(stmt)
    while name!= False:
        data.append(name)
        name=ibm_db.fetch_tuple(stmt)
    data1 = []    
    for i in range(0,len(data)):
        y = data[i][0].strip()
        data1.append(y)
    data1 = set(data1)
    data1 = list(data1)
    print(data1)
    
    
@app.route("/logout")
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return render_template("logout.html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
