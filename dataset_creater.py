# packages required
import cv2
import numpy as np
import sqlite3

faceDetect=cv2.CascadeClassifier('haarcascade_frontalface_default.xml')  #to detect the faces in camara
cam=cv2.VideoCapture(0)  # 0 for web camara

def insertorupdate(Id, Name, age):  # Function for SQLite database
    conn = sqlite3.connect("database.db")  # Connection
    cursor = conn.cursor()

    # Check if the record already exists
    cmd = "SELECT * FROM STUDENTS WHERE Id = ?"
    cursor.execute(cmd, (Id,))
    record = cursor.fetchone()

    if record:  # If record exists in the table
        cursor.execute("UPDATE STUDENTS SET Name = ?, Age = ? WHERE Id = ?", (Name, age, Id))
    else:  # If record doesn't exist in the table
        cursor.execute("INSERT INTO STUDENTS (Id, Name, Age) VALUES (?, ?, ?)", (Id, Name, age))

    conn.commit()
    conn.close()

#insert user defined values into table

Id=input('Enter your ID: ')
Name=input('Enter your Name: ')
age=input('Enter your age: ')

insertorupdate(Id,Name,age)

#detect face in web camara

sampleNum=0                      #assume there is no sample in dataset
while(True):
    ret,img=cam.read()
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)      # Image convertion  from BGR2GRAY
    faces=faceDetect.detectMultiScale(gray,1.3,5)    #scaling factors
    for(x,y,w,h) in faces:
        sampleNum=sampleNum+1       #if face is detected increments
        cv2.imwrite('dataset/user.'+str(Id)+'.'+str(sampleNum)+'.jpg',gray[y:y+h,x:x+w])
        cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),2)
        cv2.waitKey(100)            #delay time
    cv2.imshow('Face',img)       #show face detected in web camera
    cv2.waitKey(1)

    if(sampleNum>20):           #if the dataset is > 20 break
        break

cam.release()
cv2.destroyAllWindows()              # quit