#!/usr/bin/env python
# coding: utf-8

# Serial ������ ������ �����ϴ� ���

import sys

from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QBoxLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtSerialPort import QSerialPortInfo
from PyQt5.QtCore import QIODevice
from PyQt5.QtCore import QWaitCondition
from PyQt5.QtCore import QMutex
from PyQt5.QtCore import QByteArray
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import pyqtSignal

__platform__ = sys.platform


class SerialReadThread(QThread):

    # ����� ���� �ñ׳� ����
    # ���� ������ �״�θ� ���� ���ֱ� ���� QByteArray ���·� ����
    received_data = pyqtSignal(QByteArray, name="receivedData")

    def __init__(self, serial):
        QThread.__init__(self)
        self.cond = QWaitCondition()
        self._status = False
        self.mutex = QMutex()
        self.serial = serial

    def __del__(self):
        self.wait()

    def run(self):

        while True:
            self.mutex.lock()
            if not self._status:
                self.cond.wait(self.mutex)

            buf = self.serial.readAll()
            if buf:
                self.received_data.emit(buf)
            self.usleep(1)
            self.mutex.unlock()

    def toggle_status(self):
        self._status = not self._status
        if self._status:
            self.cond.wakeAll()

    @pyqtSlot(bool, name='setStatus')
    def set_status(self, status):
        self._status = status
        if self._status:
            self.cond.wakeAll()


class SerialController(QWidget):
    # �ø�����Ʈ ��� ��
    BAUDRATES = (
        QSerialPort.Baud1200,
        QSerialPort.Baud2400,
        QSerialPort.Baud4800,
        QSerialPort.Baud9600,
        QSerialPort.Baud19200,
        QSerialPort.Baud38400,
        QSerialPort.Baud57600,
        QSerialPort.Baud115200,
    )

    DATABITS = (
        QSerialPort.Data5,
        QSerialPort.Data6,
        QSerialPort.Data7,
        QSerialPort.Data8,
    )

    FLOWCONTROL = (
        QSerialPort.NoFlowControl,
        QSerialPort.HardwareControl,
        QSerialPort.SoftwareControl,
    )

    PARITY = (
        QSerialPort.NoParity,
        QSerialPort.EvenParity,
        QSerialPort.OddParity,
        QSerialPort.SpaceParity,
        QSerialPort.MarkParity,
    )

    STOPBITS = (
        QSerialPort.OneStop,
        QSerialPort.OneAndHalfStop,
        QSerialPort.TwoStop,

    )

    received_data = pyqtSignal(QByteArray, name="receivedData")
    sent_data = pyqtSignal(str, name="sentData")

    def __init__(self):
        QWidget.__init__(self, flags=Qt.Widget)
        # ���� ����
        self.gb = QGroupBox(self.tr("Serial"))
        self.cb_port = QComboBox()
        self.cb_baud_rate = QComboBox()
        self.cb_data_bits = QComboBox()
        self.cb_flow_control = QComboBox()
        self.cb_parity = QComboBox()
        self.cb_stop_bits = QComboBox()

        # �ø��� �ν��Ͻ� ����
        # �ø��� ������ ���� �� ����
        self.serial = QSerialPort()
        self.serial_info = QSerialPortInfo()
        self.serial_read_thread = SerialReadThread(self.serial)
        self.serial_read_thread.received_data.connect(lambda v: self.received_data.emit(v))
        self.serial_read_thread.start()

        self.init_widget()

    def init_widget(self):
        self.setWindowTitle("Serial Controller")
        layout = QBoxLayout(QBoxLayout.TopToBottom, parent=self)
        grid_box = QGridLayout()

        grid_box.addWidget(QLabel(self.tr("Port")), 0, 0)
        grid_box.addWidget(self.cb_port, 0, 1)

        grid_box.addWidget(QLabel(self.tr("Baud Rate")), 1, 0)
        grid_box.addWidget(self.cb_baud_rate, 1, 1)

        grid_box.addWidget(QLabel(self.tr("Data Bits")), 2, 0)
        grid_box.addWidget(self.cb_data_bits, 2, 1)

        grid_box.addWidget(QLabel(self.tr("Flow Control")), 3, 0)
        grid_box.addWidget(self.cb_flow_control, 3, 1)

        grid_box.addWidget(QLabel(self.tr("Parity")), 4, 0)
        grid_box.addWidget(self.cb_parity, 4, 1)

        grid_box.addWidget(QLabel(self.tr("Stop Bits")), 5, 0)
        grid_box.addWidget(self.cb_stop_bits, 5, 1)

        self._fill_serial_info()
        self.gb.setLayout(grid_box)
        layout.addWidget(self.gb)
        self.setLayout(layout)

    def _fill_serial_info(self):
        # �ø��� ��� ������ ������ ä���
        self.cb_port.insertItems(0, self._get_available_port())
        self.cb_baud_rate.insertItems(0, [str(x) for x in self.BAUDRATES])
        self.cb_data_bits.insertItems(0, [str(x) for x in self.DATABITS])
        flow_name = {0: "None", 1: "Hardware", 2: "Software"}
        self.cb_flow_control.insertItems(0, [flow_name[x] for x in self.FLOWCONTROL])
        parity_name = {0: "None", 2: "Even", 3: "Odd", 4: "Space", 5: "Mark"}
        self.cb_parity.insertItems(0, [parity_name[x] for x in self.PARITY])
        stop_bits_name = {1: "1", 3: "1.5", 2: "2"}
        self.cb_stop_bits.insertItems(0, [stop_bits_name[x] for x in self.STOPBITS])

    @staticmethod
    def get_port_path():

        return {"linux": '/dev/ttyS', "win32": 'COM'}[__platform__]

    def _get_available_port(self):
        available_port = list()
        port_path = self.get_port_path()

        for number in range(255):
            port_name = port_path + str(number)
            if not self._open(port_name):
                continue
            available_port.append(port_name)
            self.serial.close()
        return available_port

    def _open(self, port_name, baudrate=QSerialPort.Baud9600, data_bits=QSerialPort.Data8,
              flow_control=QSerialPort.NoFlowControl, parity=QSerialPort.NoParity, stop_bits=QSerialPort.OneStop):
        info = QSerialPortInfo(port_name)
        self.serial.setPort(info)
        self.serial.setBaudRate(baudrate)
        self.serial.setDataBits(data_bits)
        self.serial.setFlowControl(flow_control)
        self.serial.setParity(parity)
        self.serial.setStopBits(stop_bits)
        return self.serial.open(QIODevice.ReadWrite)

    def connect_serial(self):
        serial_info = {
            "port_name": self.cb_port.currentText(),
            "baudrate": self.BAUDRATES[self.cb_baud_rate.currentIndex()],
            "data_bits": self.DATABITS[self.cb_data_bits.currentIndex()],
            "flow_control": self.FLOWCONTROL[self.cb_flow_control.currentIndex()],
            "parity": self.PARITY[self.cb_parity.currentIndex()],
            "stop_bits": self.STOPBITS[self.cb_stop_bits.currentIndex()],
        }
        status = self._open(**serial_info)
        self.serial_read_thread.setStatus(status)
        return status

    def disconnect_serial(self):
        return self.serial.close()

    @pyqtSlot(bytes, name="writeData")
    def write_data(self, data):
        self.serial.writeData(data)


class Form(QWidget):
    
    def __init__(self):
        QWidget.__init__(self, flags=Qt.Widget)
        self.te = QTextEdit()
        self.pb = QPushButton("Connect")
        self.pb_send = QPushButton("Send")
        self.serial = SerialController()
        self.init_widget()

    def init_widget(self):
        
        self.setWindowTitle("Hello World")
        form_lbx = QBoxLayout(QBoxLayout.TopToBottom, parent=self)
        self.setLayout(form_lbx)

        self.pb.clicked.connect(self.slot_clicked_connect_button)
        self.serial.received_data.connect(self.read_data)
        test_data = bytes([0x02]) + bytes("GTO DATA", "utf-8") + bytes([0x03])
        self.pb_send.clicked.connect(lambda: self.serial.writeData(test_data))
        form_lbx.addWidget(self.serial)
        form_lbx.addWidget(self.te)
        form_lbx.addWidget(self.pb_send)
        form_lbx.addWidget(self.pb)

        # ���� ����ϴ� �ɼ��� �̸� ������ �д�.
        # 9600 8N1
        self.serial.cb_baud_rate.setCurrentIndex(3)
        self.serial.cb_data_bits.setCurrentIndex(3)

    @pyqtSlot(QByteArray, name="readData")
    def read_data(self, rd):
        self.te.insertPlainText(str(rd, 'ascii', 'replace'))

    @pyqtSlot(name="clickedConnectButton")
    def slot_clicked_connect_button(self):
        if self.serial.serial.isOpen():
            self.serial.disconnect_serial()
        else:
            self.serial.connect_serial()
        self.pb.setText({False: 'Connect', True: 'Disconnect'}[self.serial.serial.isOpen()])

if __name__ == "__main__":
    from PyQt5.QtWidgets import QPushButton
    from PyQt5.QtWidgets import QTextEdit
    app = QApplication(sys.argv)
    excepthook = sys.excepthook
    sys.excepthook = lambda t, val, tb: excepthook(t, val, tb)
    form = Form()
    form.show()
    exit(app.exec_())