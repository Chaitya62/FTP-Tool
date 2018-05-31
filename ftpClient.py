import ftplib
import os
import sys
import re
import time
import threading

HOST = '192.168.1.5'
PORT = 3721

USERNAME = 'chaitya'
PASSWORD = 'shah'

lock = threading.Lock()


def printr(*args, **kwargs):

        """
            To make sure only one thread writes to the STDOUT

        """

        lock.acquire()
        print(*args, **kwargs)
        lock.release()

def progress(curr, total, mn, mx):


    i = int(float((curr-4096)/(total-4096))*mx) + mn

    progress_bar = ""

    progress_bar += "["
    progress_bar += '#'*i
    progress_bar += '.'*(mx-i)
    progress_bar += ']'

    #print("{} : {}".format(curr,total))

    printr(progress_bar, end='\r')



class FTPClient(ftplib.FTP, threading.Thread):

    # can only be visiting one directory at a tiem


    def __init__(self, host, port,username, password, directory, os_path):

        ftplib.FTP.__init__(self)
        threading.Thread.__init__(self)

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.directory = directory
        self.os_path = os_path
        self.download_vars = dict()

        # connect
        self.connect(host, port)



        # login
        self.login(username, password)
        self.curr_dir = None

        self.dirs = []
        self.files = []
        self.filesizes = []


        # directory



        self.cwd(directory)




    def cwd(self, dirname):
        super().cwd(dirname)
        self.curr_dir = dirname

    def download_util(self, mess):

        absFile = self.download_vars['absFile']
        size = self.download_vars['size']
        fx = self.download_vars['fx']

        file_stats = os.stat(absFile)
        progress(file_stats.st_size, size, 1, 50)
        fx.write(mess)

        return

    def _download(self, filename, size):

        self.download_vars['absFile'] = os.path.join(self.os_path, filename)

        with open(self.download_vars['absFile'], 'wb+') as f:
            self.download_vars['fx'] = f
            self.download_vars['size'] = size
            self.retrbinary('RETR '+filename, self.download_util)
        return



    def _get_name(self, line):

        """
            utils for getting file or directory name from a LIST line

        """

        pattern = re.compile(r'[0-9]{2}:[0-9]{2}')
        line_list = line.split(' ')

        flag = False
        name = ''
        for word in line_list:

            if flag:
                name += word
                name += ' '


            if re.match(pattern, word):
                flag = True

        return name.strip()


    def _get_file_size(self, line):

        """
            utils for getting file size

        """

        pattern = re.compile(r'[0-9]{2,}')

        line_list = line.split(' ')

        for word in line_list:

            if re.match(pattern, word):
                return int(word)

        return 4096



    def _parse(self,line):

        """

        callback self.dir to get files and directories
        line: argument passed by self.dir

        """

        if line[0] == 'd':

            dirname = self._get_name(line)
            self.dirs.append(dirname)

        else:
            filename = self._get_name(line)
            file_size = self._get_file_size(line)
            self.files.append(filename)
            self.filesizes.append(file_size)



        return



    def run(self):
        self.download()

    def download(self):

        self.dir(self._parse)

        try:
            os.mkdir(self.os_path)
        except Exception:
            pass

        for i, file in enumerate(self.files):

            printr("Downloading File : {} to {}".format(file, os.path.join(self.os_path, file)))
            self._download(file, self.filesizes[i])
            print("")

        print()

        for dir in self.dirs:

            printr("Visting Directory : ", dir)

            time.sleep(0.2)
            ftpChild = FTPClient(self.host, self.port, self.username, self.password, self.directory+'/'+dir, os.path.join(self.os_path, dir))
            ftpChild.download()

        self.close()
        return











t = time.time()
ftp = FTPClient(HOST, PORT, USERNAME, PASSWORD, './Testing', '.\\testing')
ftp.download()

printr("DONE!!")
