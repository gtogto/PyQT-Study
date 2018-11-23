# 이벤트 처리
# Q버튼 생성 및 클릭 이벤트
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic

form_class = uic.loadUiType("main_window.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.pushButton 변수가 바인딩하고 있는 객체인 버튼에서 'clicked' 라는 시그널 발생
        self.pushButton.clicked.connect(self.btn_clicked)

    def btn_clicked(self):
        QMessageBox.about(self, "gto", "clicked")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
