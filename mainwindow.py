# This Python file uses the following encoding: utf-8
import sys,os,requests

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import pyqtSlot

from PyQt5 import uic
from bs4 import BeautifulSoup
import re,subprocess
from subprocess import call,PIPE

def resource_path(relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_path = resource_path("form.ui")
        uic.loadUi(self.ui_path,self)
        self.get_versions_list()
        self.version = ''
        self.kernel = ''
        self.cores = ''
        self.kernel_version.currentIndexChanged.connect(self.selectionChanged)
        self.kernel_list.currentIndexChanged.connect(self.kernel_selectionChanged)
        self.cores_list.currentIndexChanged.connect(self.get_number_of_cores)
        self.submit.clicked.connect(lambda:self.install_kernel(self.version,self.kernel))

    def get_versions_list(self):
        r = requests.get('https://mirrors.edge.kernel.org/pub/linux/kernel/')
        if r.status_code == 200:
            # Parse the HTML content
                soup = BeautifulSoup(r.content, "html.parser")

                # Find all <a> tags with href attribute pointing to directories
                directories = soup.find_all('a', href=True)

                # Extract kernel versions from the directories
                kernel_versions = [directory['href'] for directory in directories if directory.text.startswith('v')]

                self.kernel_version.addItems(kernel_versions)

        else:
            print("Failed to retrieve data from the website.")

    @pyqtSlot(int)
    def selectionChanged(self, index):
        selected_version = self.kernel_version.currentText()
        self.get_kernel_list(selected_version)
        self.version = selected_version


    @pyqtSlot(int)
    def kernel_selectionChanged(self,index):
        selected_kernel = self.kernel_list.currentText()
        self.kernel = selected_kernel



    def get_kernel_list(self,version):
        self.kernel_list.clear()
        r = requests.get('https://mirrors.edge.kernel.org/pub/linux/kernel/'+version)
        if r.status_code == 200:
            # Parse the HTML content
                soup = BeautifulSoup(r.content, "html.parser")

                # Find all <a> tags with href attribute pointing to .tar.gz files
                tar_files = soup.find_all('a', href=lambda href: href and href.endswith('.tar.gz'))

                # Extract file names from the URLs
                tar_files_names = [file['href'] for file in tar_files]
                self.kernel_list.addItems(tar_files_names)
        else:
            print("Failed to retrieve data from the website.")

    def get_number_of_cores(self):
        result,out,err = self.run_process('nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null')
        if result == 0:
            cores = int(out)
            self.cores=cores
            self.cores_list.addItems([str(i) for i in range(1,cores)])
        else:
            print(f'error! --> {result.stderr}')

    def run_process(self,cmd):
        result = subprocess.Popen(cmd,stdout=PIPE,stderr=PIPE,shell=True)
        out,err = result.communicate()
        return result.returncode,out.decode('utf-8').strip(),err.decode('utf-8').strip()


    def get_extracted_folder_name(self):
        result,out,err = self.run_process("tar -tzvf /usr/src/linux-2.3.18.tar.gz | head -n 1 | awk '{print $NF}'")
        if result == 0:
            return out
        return err

    def install_kernel(self,version,kernel):
        if  version == ''  or kernel == '' :
            print('empty fields!')
        if os.path.exists('/usr/src'):
            os.chdir('/usr/src')
        else:
            try:
                os.mkdir('/usr/src')
                os.chdir('/usr/src')
            except Exception as e :
                print(e)
        call(f"wget --continue http://kernel.org/pub/linux/kernel/{version}/{kernel}",shell=True)
        kernel_version = self.get_extracted_folder_name()
        call("tar -xvf %s" % kernel,shell=True)
        os.chdir("%s" % kernel_version)
        status,current_kernel,err=self.run_process('uname -r')
        print("current kernel version is : %s\n" % current_kernel)
        # Start by cleaning up
        call("make distclean; make mrproper", shell=True)
        self.run_process("cp /boot/config-"+current_kernel+" ./.config")
        self.run_process("scripts/config --disable SYSTEM_TRUSTED_KEYS ; scripts/config --disable SYSTEM_REVOCATION_KEYS")
        # The below commands can be merged into one
        call("y|make -j "+self.cores, shell=True)
        call("make modules_install -j "+self.cores, shell=True)
        call("make install -j "+self.cores, shell=True)
        print("Done installing the Kernel\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
