from flask import Flask, Blueprint, request, jsonify, render_template
import os
import requests
import mysql.connector
from itsdangerous import URLSafeSerializer
import random
import qrcode

#CONNECTING TO DATABASE
mydb = mysql.connector.connect(
host="localhost",
user="admin",
password="admin",
database='qrlogin',
)
mycursor = mydb.cursor()

#CREATING BLUE PRINT
bp=Blueprint('app',__name__)

#ROUTE '/'
@bp.route('/')
def index():
    return render_template('index.html')


#ROUTE '/LOGIN'
@bp.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        value=(email,)
        query="""select password from user_details where username = %s"""
        mycursor.execute(query,value)
        for row in mycursor.fetchall():
            f_password=row[0]
            if(f_password==password):
                return jsonify({'status':'success'})            
        return jsonify({'status':'fail'})
    else:
        return render_template('login.html')

#ROUTER '/SIGN UP'
@bp.route('/signup',methods=['POST','GET'])
def signup():
    if(request.method=='POST'):
        email=request.form['email']
        password=request.form['password']
        check="""select * from user_details where username = %s"""
        value=(email,)
        mycursor.execute(check,value)
        if(len(mycursor.fetchall()) > 0):
            return jsonify({'status':'fail'})
        query="""insert into user_details (username,password,token) values (%s,%s,%s)"""
        value=(email,password,'0')
        mycursor.execute(query,value)
        mydb.commit()
        return jsonify({'status':'success'})  
    else:
        return render_template('signup.html')
        


#ROUTER '/DASHBOARD'
@bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@bp.route('/createqr',methods=['POST','GET'])
def createqr():
    if(request.method=="POST"):
        email=request.form['email']
        value=(email,)
        query="""select password,token from user_details where username = %s"""
        mycursor.execute(query,value)
        token=""
        for row in mycursor.fetchall():
            password=row[0]
            token=row[1]
            print("token = " +str(token))
            if(token=="0"):
                rand_key=random.randint(1,100000)
                auth_s = URLSafeSerializer("secret"+str(rand_key), "auth")
                token = auth_s.dumps({"id": email, "name": password})
                value=(token,email)
                print("token = " +str(token))
                query="""update user_details set token = %s where username = %s"""
                mycursor.execute(query,value)
                mydb.commit()
        link="http://localhost:5000/verify?token="+token+"&email="+email
        img = qrcode.make(link)
        img.save("./app/static/"+ token +".png")
        return jsonify({'token':token,'status':'success'})
    
@bp.route('/verify',methods=['POST','GET'])
def qrlogin():
    if(request.method=="GET"):
        token=request.args.get('token')
        email=request.args.get('email')
        value=(token,email)
        query="""select * from user_details where token = %s and username = %s"""
        print(value)
        mycursor.execute(query,value)
        if(len(mycursor.fetchall()) > 0):
            value=(email,)
            query="""update user_details set token = '0' and username = %s"""
            mycursor.execute(query,value)
            mydb.commit()
            return render_template('dashboard.html',email=email)

@bp.route('/logout',methods=['POST','GET'])
def logout():
    if(request.method=="GET"):
        email=request.args.get('email')
        value=(email,)
        query="""update user_details set token = '0' and username = %s"""
        mycursor.execute(query,value)
        mydb.commit()
        return render_template('login.html')