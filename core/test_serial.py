
from serial_core.serialportcontext import SerialPortContext
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import time
import threading


class Test(QObject):
    _receive_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Test, self).__init__(parent)
        self.port = "COM3"
        self.baud = 115200

    def __data_received__(self, data):
        # self._receive_signal.emit(data)
        print(f"get the data {data}")

    def runn(self):
        self._serial_context_ = SerialPortContext(port=self.port, baud=self.baud)
        self._serial_context_.recall()
        self._serial_context_.registerReceivedCallback(self.__data_received__)
        self._serial_context_.open()

        time.sleep(3)
        self._serial_context_.close()


if __name__ == "__main__":

    import sys
    app = QApplication(sys.argv)  # You still need a QApplication object.
    a = Test()
    a.runn()
    sys.exit(app.exec())
    # t = Test()
    # t.runn()


