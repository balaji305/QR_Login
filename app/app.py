from flask import Flask, Blueprint, request, jsonify, render_template
import os
import requests
import mysql.connector

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
            print(row[0])
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
        query="""insert into user_details (username,password) values (%s,%s)"""
        value=(email,password)
        mycursor.execute(query,value)
        mydb.commit()
        return jsonify({'status':'success'})  
    else:
        return render_template('signup.html')
        


#ROUTER '/DASHBOARD'
@bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
