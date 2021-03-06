#coding=utf-8
import tornado.web
import os
import StringIO
import numpy
import cv2
from PIL import Image
import base64
from datetime import datetime

import face_detect
import face_recognise
import pic_pretreatment
import dbhandler
import checkin

TIMEFORMAT = "%Y-%m-%d %X"

# Manhattan Distance
def L1(v1,v2):
    return sum([abs(v1[i]-v2[i]) for i in range(len(v1))])

class RecogniseHandler(tornado.web.RequestHandler):
    def post(self):
        pic = self.get_argument("pic")
        sid = self.get_argument("sid")
        picData = base64.b64decode(pic)
        buf = StringIO.StringIO()
        buf.write(picData)
        buf.seek(0)
        # face detection
        region = face_detect.process(imgData = buf)
        # pretreatment
        if region:
            cvImage = pic_pretreatment.process(region)
            cv2Data = numpy.asarray(cvImage[:])
            # get mean and eigenvectors from DB
            db = dbhandler.DBHandler()
            try:
               mean, eigenvectors = db.get_pca()
            except:
                print "Error: Failed to get mean and eigenvectors from DB"
            # project
            # convert mean and eigenvectors to numpy array
            mean_list = [float(i) for i in mean.split(" ")]
            mean_numpy = numpy.asarray(mean_list[:]).reshape(1, -1)

            vec_strings = [s for s in eigenvectors.split("|")]
            eigenvectors_list = []
            for vec_str in vec_strings:
                vec_list = [float(i) for i in vec_str.split(" ")]
                eigenvectors_list.append(vec_list)
            eigenvectors_numpy = numpy.asarray(eigenvectors_list[:]).reshape(len(eigenvectors_list),-1)

            # get eigenface
            eigenface = face_recognise.get_eigenface(mean_numpy, eigenvectors_numpy, cvData = cv2Data)
            # compute distance
            staff = db.get_staff(sid = sid)
            if len(staff) == 0:
                self.write("-2")  # sid is not exist
                return False
            eface_str = staff[0]["eigenface"]
            staff_dis = float(staff[0]["distance"])
            eface = [float(i) for i in eface_str.split(" ")]
            dis = L1(eigenface[0], eface)
            '''
            print eigenface[0]
            print eface
            print dis
            '''
            if dis <= staff_dis:
                image_path = "static/records/checkin/%s_%s.jpg" % (sid, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
                buf.seek(0)
                image = Image.open(buf)
                image.save(image_path, "JPEG", quality = 80)
                msg = checkin.checkin(sid, image_path)
                if msg[1] == -1 or msg[1] == 0:
                    os.remove(image_path)   # check in error
                reponse_msg = str(msg[1]) + '|' + msg[0]
                self.write(reponse_msg)
                print msg[0]
            else:
                self.write("-1")
        else:
            self.write("-1")


class UploadIMGHandler(tornado.web.RequestHandler):
    def post(self):
        # get picture and sid
        pic = self.get_argument("pic")
        sid = self.get_argument("sid")

        picData = base64.b64decode(pic)
        buf = StringIO.StringIO()
        buf.write(picData)
        buf.seek(0)
        face_tmp_path = "static/records/faces/%s_tmp.jpg" % sid
        grayface_tmp_path = "static/records/grayfaces/%s_tmp.jpg" % sid

        # face detection
        region = face_detect.process(imgData = buf, outfile = face_tmp_path)
        # pretreatment
        if region:
            pic_pretreatment.process(region, 
                                    powfile = grayface_tmp_path,
                                    )
            self.write("success")
        else:
            self.write("failed")

class AddStaffHandler(tornado.web.RequestHandler):
    def post(self):
        # get info
        sid = self.get_argument("sid")
        pwd = self.get_argument("pwd")
        name = self.get_argument("name")
        idnumber = self.get_argument("idnumber")
        age = int(self.get_argument("age"))
        department = int(self.get_argument("department"))
        ondutytime = self.get_argument("ondutytime")
        offdutytime = self.get_argument("offdutytime")
        
        grayface_tmp_path = "static/records/grayfaces/%s_tmp.jpg" % sid
        db = dbhandler.DBHandler()

        # write staff information to DB
        try:
            db.add_staff(sid = sid, pwd = pwd, name = name, idnumber = idnumber, age = age, department = department, ondutytime = ondutytime, offdutytime = offdutytime)
        except:
            print "Error: Add staff information failed. sid = %s" % sid
            self.write("failed")
            return False

        # store new face picture to DB
        grayface = cv2.imread(grayface_tmp_path, 0)
        grayface = grayface.reshape(100 * 100)
        grayface_str = ""
        for p in grayface:
            grayface_str += str(p)
            grayface_str += " "
        grayface_str = grayface_str[:-1]
        try:
            db.store_face(sid, grayface_str)
        except:
            print "Error: Store image to DB failed. sid = %s" % sid
            self.write("failed")
            return False

        # Compute PCA - Training
        mean, eigenvectors = face_recognise.computePCA()

        # Update all staffs' eigenface
        staffs = db.look_table("staff")
        efaces = {}
        for staff in staffs:
            sid = staff["sid"]
            try:
                records = db.get_face(sid)
            except:
                print "Error: Get image from DB failed. sid = %s" % sid
                self.write("failed")
                return False
            nm = numpy.fromstring(records[0]['img'], dtype = numpy.uint8, sep = " ")
            nm = nm.reshape(100, -1)
            eigenface = face_recognise.get_eigenface(mean, eigenvectors, cvData = nm)
            l = ["%.8f" % number for number in eigenface[0]]
            eigenface_str = " ".join(l)
            try:
                db.update_eigenface(sid, eigenface_str)
            except:
                print "Error: Write eigenface to DB failed. sid = %s" % sid
                self.write("failed")
                return False
            efaces[sid] = eigenface

        # Update all staffs' distance
        ratio = 2.0
        for sid in efaces:
            theface = efaces[sid]
            min = 10000000.0
            for other in efaces:
                if other != sid:
                    dis = L1(theface[0], efaces[other][0])
                    if dis < min:
                        min = dis
            try:
                db.update_distance(sid, min / ratio)
            except:
                print "Error: Write distance to DB failed. sid = %s" % sid
                self.write("failed")
                return False

        # Write mean and eigenvectors to DB
        # mean to string
        m = ["%.8f" % number for number in mean[0]]
        mean_str = " ".join(m)
        # eigenvectors to string
        eigenvectors_str = ""
        for vec in eigenvectors:
            v = ["%.8f" % number for number in vec]
            vec_str = " ".join(v)
            eigenvectors_str += vec_str
            eigenvectors_str += "|"
        eigenvectors_str = eigenvectors_str[:-1]
        try:
            db.update_pca(mean_str, eigenvectors_str)
        except:
            print "Error: Update mean and eigenvectors to DB failed. "
            self.write("failed")
            return False

        os.remove(grayface_tmp_path)
        self.write("success")

# staff manage
class AuthBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("sid")

class LoginHandler(AuthBaseHandler):
    def get(self):
        self.render("static/html/login.html")

    def post(self):
        db = dbhandler.DBHandler()
        sid = self.get_argument("sid")
        pwd = self.get_argument("pwd")
        check = db.staff_login(sid, pwd)
        if check == 1:
            self.set_secure_cookie("sid", sid)
            self.write("success")
        elif check == -1:
            self.write("siderror")
        elif check == 0:
            self.write("pwderror")

class LogoutHandler(AuthBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.clear_cookie("sid")
        self.redirect("/login")

class RecordInfoHandler(AuthBaseHandler):
    @tornado.web.authenticated
    def post(self):
        db = dbhandler.DBHandler()
        sid = tornado.escape.xhtml_escape(self.current_user)
        year = self.get_argument("year")
        month = self.get_argument("month")
        day = self.get_argument("day")
        rtype = self.get_argument("type")
        time1 = "%s-%s-%d 00:00:00" % (year, month, int(day))
        time2 = "%s-%s-%d 23:59:59" % (year, month, int(day))
        records = db.get_checkin_records(sid, time1, time2)
        for r in records:
            if r['rtype'] == int(rtype):
                self.write(str(r['rtime']))

# admin manage
class AuthAdminBaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("name")

class LoginAdminHandler(AuthAdminBaseHandler):
    def get(self):
        self.render("static/html/login_admin.html")

    def post(self):
        db = dbhandler.DBHandler()
        name = self.get_argument("name")
        pwd = self.get_argument("pwd")
        check = db.admin_login(name, pwd)
        if check == 1:
            self.set_secure_cookie("name", name)
            self.write("success")
        elif check == -1:
            self.write("aiderror")
        elif check == 0:
            self.write("pwderror")

class LogoutAdminHandler(AuthAdminBaseHandler):
    def get(self):
        if self.current_user:
            name = tornado.escape.xhtml_escape(self.current_user)
            self.clear_cookie("name")
        self.redirect("/login_admin")

class CheckSIDHandler(AuthAdminBaseHandler):
    def post(self):
        if self.current_user:
            db = dbhandler.DBHandler()
            sid = self.get_argument("sid")
            records = db.get_staff(sid)
            if len(records) == 0:
                self.write("nosid")
            else:
                self.write("hadsid")
        else:
            self.redirect("/login_admin")



