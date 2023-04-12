import mysql.connector
import os
db=os.environ['RDS_DB_NAME']
user=os.environ['RDS_USERNAME']
password=os.environ['RDS_PASSWORD']
host=os.environ['RDS_HOSTNAME']
port=os.environ['RDS_PORT']
def dbconn():
    mysql_con=mysql.connector.connect(host=host,user=user,password=password,db=db,port=port)
    with mysql_con as conn:
        cursor=conn.cursor()
        cursor.execute('create table if not exists students(rollno varchar(6) primary key,name varchar(30),std_group varchar(10),password varchar(15),email varchar(70))')
        cursor.execute('create table if not exists notes(nid int primary key auto_increment,rollno varchar(6),title varchar(30),content text,date datetime default now(),foreign key(rollno) references students(rollno))')
        cursor.execute('create table if not exists files(fid int primary key auto_increment,rollno varchar(6),filename varchar(30),filedata longblob,date datetime default now(),foreign key(rollno) references students(rollno))')

