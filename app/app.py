from flask import Flask, Blueprint, request, jsonify, render_template
import os
import requests
import mysql.connector
from itsdangerous import URLSafeSerializer
import random
import qrcode
import hashlib
from dotenv import load_dotenv, dotenv_values
import base64
from app import crypt_ops


#LOADING ENVIRONMENT VARIABLES
load_dotenv()
config = dotenv_values(".env")


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
            if(token=="0"):
                rand_key=random.randint(1,100000)
                auth_s = URLSafeSerializer("secret"+str(rand_key), "auth")
                token = auth_s.dumps({"id": email, "name": password})
                value=(token,email)
                query="""update user_details set token = %s where username = %s"""
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
    
@bp.route('/verify',methods=['POST','GET'])
def qrlogin():
    if(request.method=="GET"):
        ciphertext=request.args.get('msg').encode()
        ciphertext=base64.urlsafe_b64decode(ciphertext)
        key=config['AES_KEY']
        key=base64.urlsafe_b64decode(key)
        plain_txt = crypt_ops.dec(key, ciphertext)
        plain_txt=plain_txt.decode()
        print("P2=",plain_txt)
        plain_txt=plain_txt.split('&')
        token=plain_txt[0].split('=')[1]
        email=plain_txt[1].split('=')[1]
        value=(token,email)
        query="""select * from user_details where token = %s and username = %s"""
        mycursor.execute(query,value)
        if(len(mycursor.fetchall()) > 0):
            value=(email,)
            query="""update user_details set token = '0' and username = %s"""
            mycursor.execute(query,value)
            mydb.commit()
            return render_template('dashboard.html',email=email)

@bp.route('/logout',methods=['POST','GET'])
def logout():
    if(request.method=="POST"):
        email=request.args.get('email')
        value=(email,)
        query="""update user_details set token = '0' and username = %s"""
        mycursor.execute(query,value)
        mydb.commit()
        return ({'status':'success'})