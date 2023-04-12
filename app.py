from flask import Flask,request,redirect,render_template,url_for,flash,session,send_file
from flask_session import Session
from otp import genotp
import mysql.connector
from cmail import sendmail
import random
from io import BytesIO
import os
app=Flask(__name__)
app.secret_key='*67@hjyjhk'
app.config['SESSION_TYPE']='filesystem'
db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
mydb=mysql.connector.connect(host=host,user=user,password=password,db=db,port=port)
#mydb=mysql.connector.connect(host='localhost',user='root',password='Eswar@2001',db='spm')
with mysql.connector.connect(host=host,user=user,password=password,db=db,port=port) as conn:
    cursor=conn.cursor()
    cursor.execute('create table if not exists students(rollno varchar(6) primary key,name varchar(30),std_group varchar(10),password varchar(15),email varchar(70))')
    cursor.execute('create table if not exists notes(nid int primary key auto_increment,rollno varchar(6),title varchar(30),content text,date datetime default now(),foreign key(rollno) references students(rollno))')
    cursor.execute('create table if not exists files(fid int primary key auto_increment,rollno varchar(6),filename varchar(30),filedata longblob,date datetime default now(),foreign key(rollno) references students(rollno))')
Session(app)
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/registration',methods=['GET','POST'])
def register():
    print(url_for('login'))
    if request.method=='POST':
        rollno=request.form['rollno']
        name=request.form['name']
        group=request.form['group']
        password=request.form['password']
        code=request.form['code']
        email=request.form['email']
        #define college code
        ccode='sdmsmkpbsc$#23'
        if ccode==code:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select rollno from students')
            data=cursor.fetchall()
            cursor.execute('SELECT email from students')
            edata=cursor.fetchall()
            #print(data)
            if (rollno,) in data:
                flash('User already already exists')
                return render_template('register.html')
            if (email,) in edata:
                flash('Email id already already exists')
                return render_template('register.html')
    
            cursor.close()
            otp=genotp()
            sendmail(email,otp)
            return render_template('otp.html',otp=otp,rollno=rollno,name=name,group=group,password=password,email=email)
        else:
            flash('Invalid college code')
            return render_template('register.html') 
    return render_template('register.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        rollno=request.form['id']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from students where \
rollno=%s and password=%s',[rollno,password])
        count=cursor.fetchone()[0]
        if count==0:
            flash('Invalid roll no or password')
            return render_template('login.html')
        else:
            session['user']=rollno
            return redirect(url_for('home'))
    return render_template('login.html')
@app.route('/Studenthome')
def home():
    if session.get('user'):
        return render_template('home.html')
    else:
        #implement flash
        return redirect(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('index'))
    else:
        flash('already logged out!')
        return redirect(url_for('login'))
        

@app.route('/otp/<otp>/<rollno>/<name>/<group>/<password>/<email>',methods=['GET','POST'])
def otp(otp,rollno,name,group,password,email):
    if request.method=='POST':
        uotp=request.form['otp']
        if otp==uotp:
            cursor=mydb.cursor(buffered=True)
            lst=[rollno,name,group,password,email]
            query='insert into students \
values(%s,%s,%s,%s,%s)'
            cursor.execute(query,lst)
            mydb.commit()
            cursor.close()
            flash('Details registered')
            
            return redirect(url_for('login'))
        else:
            flash('Wrong otp')
            return render_template('otp.html',otp=otp,rollno=rollno,name=name,group=group,password=password,email=email)
@app.route('/noteshome')
def notehome():
    if session.get('user'):
        rollno=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notes where rollno=%s',[rollno])
        notes_data=cursor.fetchall()
        print(notes_data)
        cursor.close()
        return render_template('addnotetable.html',
                               data=notes_data)
    else:
        return redirect(url_for('login'))
@app.route('/addnotes',methods=['GET','POST'])
def addnote():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            cursor=mydb.cursor(buffered=True)
            rollno=session.get('user')
            cursor.execute('insert into notes\
(rollno,title,content) values(%s,%s,%s)',[rollno,title,content])
            mydb.commit()
            cursor.close()
            flash(f'{title} added successfully')
            return redirect(url_for('notehome'))
            
        return render_template('notes.html')
    else:
        return redirect(url_for('login'))
@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select title,content from notes where nid=%s',[nid])
    data=cursor.fetchone()
    return render_template('notesview.html',data=data)
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,content from notes where nid=%s',[nid])
        data=cursor.fetchone()
        cursor.close()
        if request.method=='POST':
                title=request.form['title']
                content=request.form['content']
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update notes set \
title=%s,content=%s where nid=%s',[title,content,nid])
                mydb.commit()
                cursor.close()
                flash('Notes updated successfully')
                return redirect(url_for('notehome'))
                
        return render_template('updatenotes.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/deletenotes/<nid>')
def deletenotes(nid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('delete from notes \
where nid=%s',[nid])
    mydb.commit()
    cursor.close()
    flash('Notes deleted successfully')
    return redirect(url_for('notehome'))
@app.route('/fileshome')
def fileshome():
    if session.get('user'):
        rollno=session.get('user')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('SELECT fid,filename,date from files where rollno=%s',[rollno])
        data=cursor.fetchall()
        cursor.close()
        return render_template('fileuploadtable.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/filehandling',methods=['POST'])
def filehandling():
    file=request.files['file']
    filename=file.filename
    bin_file=file.read()
    rollno=session.get('user')
    cursor=mydb.cursor(buffered=True)
    cursor.execute('insert into files(rollno,\
filename,filedata) values(%s,%s,%s)',[rollno,filename,bin_file])
    mydb.commit()
    cursor.close()
    flash(f'{filename} uploaded successfully')
    return redirect(url_for('fileshome'))
    
@app.route('/viewfile/<fid>')
def viewfile(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select filename,filedata from files where fid=%s',[fid])
        data=cursor.fetchone()
        cursor.close()
        filename=data[0]
        bin_file=data[1]
        byte_data=BytesIO(bin_file)
        #return send_file(byte_data,download_name=filename,as_attachment=True)
        return send_file(byte_data,download_name=filename,as_attachment=False)
    else:
        return redirect(url_for('login'))
@app.route('/filedelete/<fid>')
def filedelete(fid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('delete from files \
where fid=%s',[fid])
    mydb.commit()
    cursor.close()
    flash('File deleted successfully')
    return redirect(url_for('fileshome'))
@app.route('/forgetpassword',methods=['GET','POST'])
def forget():
    if request.method=='POST':
        rollno=request.form['id']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select rollno from students')
        data=cursor.fetchall()
        if (rollno,) in data:
            cursor.execute('select email from students where rollno=%s',[rollno])
            data=cursor.fetchone()[0]
            cursor.close()
            session['pass']=rollno
            sendmail(data,subject='Reset password',body=f'Reset the password here -{request.host+url_for("createpassword")}')
            flash('reset link sent to your mail')
            return redirect(url_for('login'))
        else:
            return 'Invalid user id'
    return render_template('forgot.html')
@app.route('/createpassword',methods=['GET','POST'])
def createpassword():
    if session.get('pass'):
        if request.method=='POST':
            oldp=request.form['npassword']
            newp=request.form['cpassword']
            if oldp==newp:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update students set password=%s where rollno=%s',[newp,session.get('pass')])
                mydb.commit()
                flash('Password changed successfully')
                return redirect(url_for('login'))
            else:
                flash('New password and confirm passwords should be same')
                return render_template('newpassword.html')
        return render_template('newpassword.html')
    else:
        return redirect(url_for('login'))
if __name__=="__main__":
    app.run()

































