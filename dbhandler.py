import tornado.database

DEFAULT_ON_DUTY_TIME = "8:30"
DEFAULT_OFF_DUTY_TIME = "17:30"

# Fix time_zone problem
class Connection(tornado.database.Connection):
    def __init__(self, mysql_host, mysql_database, mysql_user, mysql_password):
        super(Connection, self).__init__(
            host=mysql_host,
            database=mysql_database,
            user=mysql_user,
            password=mysql_password
        )
        self._db_args["init_command"] = 'SET time_zone = "+8:00"'
        try:
            self.reconnect()
        except Exception:
            logging.error("Cannot connect to MySQL on %s", self.host,
                          exc_info=True)

class DBHandler:
    # Init the connection
    def __init__(self):
        self.db = Connection("localhost", "nevermore", "root", "")
    
    # Login check 
    def staff_login(self, sid, pwd):
        if self.db.execute_rowcount("SELECT * FROM staff WHERE sid = '%s'" % (sid)) == 0:
            return -1
        if self.db.execute_rowcount("SELECT * FROM staff WHERE sid = '%s' and pwd = '%s'" % (sid, pwd)) == 1:
            return 1
        else:
            return 0

    # Admin Login check 
    def admin_login(self, name, pwd):
        if self.db.execute_rowcount("SELECT * FROM admin WHERE name = '%s'" % (name)) == 0:
            return -1
        if self.db.execute_rowcount("SELECT * FROM admin WHERE name = '%s' and pwd = '%s'" % (name, pwd)) == 1:
            return 1
        else:
            return 0
    
    # Look up the table
    def look_table(self, table):
        return self.db.query("SELECT * FROM %s" % table)
        
    # Add one staff in db
    def add_staff(self, sid, pwd, name, idnumber, age, department,
                  ondutytime = DEFAULT_ON_DUTY_TIME, 
                  offdutytime = DEFAULT_OFF_DUTY_TIME, 
                  distance = 0.0, 
                  eigenface = " ",
                 ):
        self.db.execute("INSERT INTO staff (sid, pwd, name, idnumber, age, department, ondutytime, offdutytime, distance, eigenface) VALUES ('%s', '%s', '%s', '%s', %d, %d, '%s', '%s', %f, '%s')" % (sid, pwd, name, idnumber, age, department, ondutytime, offdutytime, distance, eigenface))

    #Get one staff's info
    def get_staff(self, sid):
        return self.db.query("SELECT * FROM staff WHERE sid = '%s'" % (sid))

    #Update one staff's eigenface in db
    def update_eigenface(self, sid, eigenface):
        self.db.execute("UPDATE staff SET eigenface = '%s' WHERE sid = '%s'" % (eigenface, sid))

    #Update one staff's distance in db
    def update_distance(self, sid, distance):
        self.db.execute("UPDATE staff SET distance = %f WHERE sid = '%s'" % (distance, sid))

    #Delete one staff in db
    def del_staff(self, sid):
        self.db.execute("DELETE FROM staff WHERE sid = '%s'" % sid)
        
    #Add one log in db
    def add_log(self, uid, ltype, content):
        self.db.execute("INSERT INTO log (uid, ltype, content) VALUES ('%s', %d, '%s',)" % (uid, ltype, content))

    #Update mean and eigenvectors
    def update_pca(self, mean, eigenvectors):
        self.db.execute("UPDATE setting SET value = '%s' WHERE skey = 'mean'" % (mean))
        self.db.execute("UPDATE setting SET value = '%s' WHERE skey = 'eigenvectors'" % (eigenvectors))

    # Get mean and eigenvectors
    def get_pca(self):
        mean = self.db.query("SELECT value FROM setting WHERE skey = 'mean'")
        eigenvectors = self.db.query("SELECT value FROM setting WHERE skey = 'eigenvectors'")
        return (mean[0]['value'], eigenvectors[0]['value'])

    # Store face image to DB
    def store_face(self, sid, img_string):
        self.db.execute("INSERT INTO image (sid, img) VALUES ('%s', '%s')" % (sid, img_string))

    # Get face image by sid
    def get_face(self, sid):
        return self.db.query("SELECT * FROM image WHERE sid = '%s'" % (sid))

    # Get checkin records for a period time
    def get_checkin_records(self, sid, time1, time2):
        return self.db.query("SELECT * FROM record WHERE sid = '%s' and rtime >= '%s' and rtime <= '%s'" % (sid, time1, time2))

    # Add checkin record in db
    def add_checkin_record(self, sid, rtype, rstate, rimage):
        self.db.execute("INSERT INTO record (sid, rtype, rstate, rimage) VALUES ('%s', %d, %d, '%s')" % (sid, rtype, rstate, rimage))

if __name__ == '__main__':
    db = DBHandler()
    for r in db.get_checkin_records('224', '2013-03-26 00:00:00', '2013-3-30 23:59:59'):
        print r['rtime']
