# This Python file uses the following encoding: utf-8
import sys,os,requests

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import pyqtSlot

from PyQt5 import uic
from bs4 import BeautifulSoup
import re,subprocess
from subprocess import call

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
        self.selected_item = ''
        self.get_versions_list()
        self.kernel_version.currentIndexChanged.connect(self.selectionChanged)
        self.kernel_list.currentIndexChanged.connect(self.kernel_selectionChanged)
        self.get_number_of_cores()
        self.version = ''
        self.kernel = ''
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
        self.selected_item = self.kernel_version.currentText()
        self.get_kernel_list(self.selected_item)
        self.version = self.selected_item

    @pyqtSlot(int)
    def kernel_selectionChanged(self,index):
        self.selected_item = self.kernel_list.currentText()
        self.kernel = self.selected_item



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
        result = subprocess.run('nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null',capture_output=True,text=True,shell=True)
        if result.returncode == 0:
            cores = int(result.stdout.strip())
            self.cores_list.addItems([str(i) for i in range(1,cores)])
        else:
            print(f'error! --> {result.stderr}')

    def install_kernel(self,version,kernel):
        if  version == ''  or kernel == '' :
            print('empty fields!')
        if os.path.exists('/usr/src'):
            os.chdir('/usr/src')
        else:
            try:
                os.mkdir('/usr/src')
            except Exception as e :
                print(e)
        call(f"wget --continue http://kernel.org/pub/linux/kernel/{version}/{kernel}",shell=True)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
