import os, datetime

sh_logdir = os.getenv("sh_logdir","/tmp")

class mLog:
    def __init__(self,sensor):
        date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.logfile = f"{sh_logdir}/{sensor}-{date}.mLog"
        self.filehandle = open(self.logfile,"w")

    def log(self,s):
        self.filehandle.write("%s %s\n" % (datetime.datetime.now().strftime("%H:%M:%S"),s))
        self.filehandle.flush()

        