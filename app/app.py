from flask import Flask, Blueprint, request, jsonify, render_template, redirect, url_for
import os
import requests
import mysql.connector
from itsdangerous import URLSafeSerializer
import random
import qrcode
import hashlib
from dotenv import dotenv_values, load_dotenv
import base64
from app import crypt_ops
import socket

#LOADING ENVIRONMENT VARIABLES
load_dotenv()
config = dotenv_values(".env")


#CONNECTING TO DATABASE
mydb = mysql.connector.connect(
host="localhost",
user="admin",
password="admin",
database='qrlogin',
auth_plugin='mysql_native_password'
)
mycursor = mydb.cursor()

#CREATING BLUE PRINT
bp=Blueprint('app',__name__)

#ROUTE '/'
@bp.route('/')
def index():
    return render_template('login.html')

#ROUTE '/LOGIN'
@bp.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        password=hashlib.md5(password.encode()).hexdigest()
        value=(email,)
        query="""select password from user_details where username = %s"""
        mycursor.execute(query,value)
        for row in mycursor.fetchall():
            f_password=row[0]
            if(f_password==password):
                return jsonify({'status':'success'})
            else:
                return jsonify({'status':'invalid'})         
        return jsonify({'status':'fail'})
    else:
        return render_template('login.html')

#ROUTER '/SIGN UP'
@bp.route('/signup',methods=['POST','GET'])
def signup():
    if(request.method=='POST'):
        email=request.form['email']
        password=request.form['password']
        password=hashlib.md5(password.encode()).hexdigest()
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

#ROUTER '/CREATEQR'
@bp.route('/createqr',methods=['POST','GET'])
def createqr():
    if(request.method=="POST"):
        email=request.form['email']
        if(email == 'null'):
            return jsonify({'status':'fail'})
        value=(email,)
        query="""select password,token from user_details where username = %s"""
        mycursor.execute(query,value)
        token=""
        for row in mycursor.fetchall():
            password=row[0]
            token=row[1]
            if(token=="0"):
                rand_key=random.randint(1,100000)
                otp=random.randint(100000,999999)
                auth_s = URLSafeSerializer("secret"+str(rand_key), "auth")
                token = auth_s.dumps({"id": email, "name": password})
                value=(token,otp,email)
                query="""update user_details set token = %s, otp = %s where username = %s"""
                mycursor.execute(query,value)
                mydb.commit()

        key=config['AES_KEY']
        key=base64.urlsafe_b64decode(key)
        link="http://localhost:5000/verify?"
        plain_txt="token="+token+"&email="+email
        plain_txt=plain_txt.encode()
        
        cipher_text = crypt_ops.enc(key, plain_txt)
        cipher_text = base64.urlsafe_b64encode(cipher_text).decode('utf-8')
        link=link+"msg="+cipher_text
        img = qrcode.make(link)
        img.save("./app/static/"+ token +".png")

        return jsonify({'token':token,'link':link,'status':'success'})
    
#ROUTER '/VERIFY'
@bp.route('/verify',methods=['POST','GET'])
def qrlogin():
    if(request.method=="GET"):
        ciphertext=request.args.get('msg').encode()
        ciphertext=base64.urlsafe_b64decode(ciphertext)
        key=config['AES_KEY']
        key=base64.urlsafe_b64decode(key)
        plain_txt = crypt_ops.dec(key, ciphertext)
        plain_txt=plain_txt.decode()
        plain_txt=plain_txt.split('&')
        token=plain_txt[0].split('=')[1]
        email=plain_txt[1].split('=')[1]
        hostname = socket.gethostname()
        IPAddr = socket.gethostbyname(hostname)
        
        print("Your Computer Name is:" + hostname)
        print("Your Computer IP Address is:" + IPAddr)

        while(email[-1] != 'm'):
            email=email[:-1]
        value=(token,email)
        query="""select * from user_details where token = %s and username = %s"""
        mycursor.execute(query,value)
        if(len(mycursor.fetchall()) > 0):
            value=(hostname,IPAddr,email)
            query="""update user_details set token = '0', hostname = %s, hostip = %s where username = %s"""
            mycursor.execute(query,value)
            mydb.commit()
            return redirect(url_for('app.otp',email=email,hostname=hostname,addr=str(IPAddr)))

@bp.route('/logout',methods=['POST','GET'])
def logout():
    if(request.method=="POST"):
        email=request.args.get('email')
        value=(email,)
        query="""update user_details set token = '0' and username = %s"""
        mycursor.execute(query,value)
        mydb.commit()
        return ({'status':'success'})

@bp.route('/otp',methods=['POST','GET'])
def otp():
    return render_template('otp.html')

@bp.route('/fetch',methods=['POST','GET'])
def fetch():
    email=request.form['email']
    value=(email,)
    query="""select hostname,hostip, otp from user_details where username = %s"""
    mycursor.execute(query,value)
    for row in mycursor.fetchall():
        return ({'status':'success', 'hostname':row[0], 'hostip':row[1], 'otp':row[2]})

@bp.route('/verifyotp', methods=['POST','GET'])
def verifyotp():
    email=request.form['email']
    otp=request.form['otp']
    value=(email,)
    query="""select otp from user_details where username = %s"""
    mycursor.execute(query,value)
    for row in mycursor.fetchall():
        if(row[0]==otp):
            query="""update user_details set hostname = NULL, hostip = NULL, otp = NULL where username = %s"""
            mycursor.execute(query,value)
            mydb.commit()
            return ({'status':'success'})
    return({'status':'failed'})