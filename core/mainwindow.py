# -*- coding: utf-8 -*-

__author__ = "Yu-Sheng Lin"
__copyright__ = "Copyright (C) 2016-2020"
__license__ = "AGPL"
__email__ = "pyquino@gmail.com"

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot
from .classes import Thread_wait_forController, Thread_slect_focus, DisplayFilter
from core.serial_core.serialportcontext import SerialPortContext

import numpy as np
import math
import time
from . import icon

import TIS.Imaging
from System import TimeSpan


class MainWindow(QMainWindow):

    test_pixmap = pyqtSignal(object)
    _receive_signal = pyqtSignal(str)
    
    def __init__(self, parent = None):
        super(MainWindow, self).__init__()
        loadUi("core/mainwindow.ui", self)
        self.__init_setting()
        self._add_action()
        self.show()
        self.ic = TIS.Imaging.ICImagingControl()
        # for live display
        displayFilter = DisplayFilter()
        displayFilter.signals.display.connect(self.OnDisplay)
        self.ic.DisplayFrameFilters.Add(self.ic.FrameFilterCreate(displayFilter))

        self.snapsink = TIS.Imaging.FrameSnapSink(TIS.Imaging.MediaSubtypes.RGB32)
        self.ic.Sink = self.snapsink
        # Create the sink for snapping images on demand.
        self.ic.LiveDisplay = True
        self.flag = True
        
        self.test = Thread_wait_forController("C:/Users/smpss/kmol/Pyquino")
        self.test_pixmap.connect(self.test.ttt)

        self.brain_focus = Thread_slect_focus(self.test)
        self.test_pixmap.connect(self.brain_focus.ttt)

        self.test.laplacian_signal.connect(self.brain_focus.get_laplacin_value)
        self.count = 0

        self._serial_context_ = SerialPortContext(port="COM0", baud=0)
        self._receive_signal.connect(self.test.test_received)

        # test for for the form
        # self.image_btn.setIcon(QIcon("images/control_xy.png"))
        # setting Qslider
        self.servo_slider.valueChanged.connect(self.sliderChanged)
        self.servo_slider.sliderPressed.connect(self.sldDisconnect)
        self.servo_slider.sliderReleased.connect(self.sldReconnect)

        try:
            self.ic.LoadDeviceStateFromFile("device.xml", True)
            if self.ic.DeviceValid is True:
                self.ic.LiveStart()
        except Exception as ex:
            print(ex)
            pass

    def finff(self):
        print("finished")

    def __init_setting(self):
        # Load IC Imaging Control .NET
        # Import the IC Imaging Control namespace.
        pass

    def _serial_button_Setting(self):

        tmp = {
            self.left_up: [-1, 1],
            self.yAxisup: [0, 1],
            self.right_up: [1, 1],
            self.xAxisrigh: [1, 0],
            self.right_down: [1, -1],
            self.yAxisdown: [0, -1],
            self.left_down: [-1, -1],
            self.xAxisleft: [-1, 0],
        }
        self.numberz = self.stepbox.value()

        def make_func(btn):
            @pyqtSlot()
            def dynamic():
                x = f"{tmp[btn][0] * self.stepbox.value()}"
                y = f"{tmp[btn][1] * self.stepbox.value()}"
                f = self.feedbox.value()
                data = f"G91\nG1X{x}Y{y}F{f}\nG90\nM114\n"
                self.__test__send(data)
            return dynamic
        for i, btn in enumerate(tmp):
            btn.setEnabled(True)
            f = make_func(btn)
            btn.clicked.connect(f)
            # print(btn, f"-> {tmp[btn]}")

        tmps = {
            self.machine_homex_btn: "X",
            self.machine_homey_btn: "Y",
            self.machine_homez_btn: "Z",
        }

        def make_func_home(btn):
            @pyqtSlot()
            def d():
                data = f"G28 {tmps[btn]}0\nM114\n"
                self.__test__send(data)
            return d

        for i, btn in enumerate(tmps):
            btn.setEnabled(True)
            f = make_func_home(btn)
            btn.clicked.connect(f)
        # self.xAxisrigh
        # self.right_down
        # self.yAxisdown
        # self.left_down
        # self.xAxisleft

    # @pyqtSlot()
    # def on_left_up_cliecked(self):

    def _add_action(self):
        # Create the menu
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')

        exitAct = QAction("&Exit", self)
        exitAct.setStatusTip("Exit program")
        # exitAct.triggered.connect(self.Close)
        fileMenu.addAction(exitAct)

        deviceMenu = mainMenu.addMenu('&Device')
        devselAct = QAction("&Select", self)
        devselAct.triggered.connect(self.SelectDevice)
        deviceMenu.addAction(devselAct)

        devpropAct = QAction("&Properties", self)
        devpropAct.triggered.connect(self.ShowProperties)
        deviceMenu.addAction(devpropAct)

        snapAct = QAction("Snap &Image", self)
        snapAct.triggered.connect(self.SnapImage)
        deviceMenu.addAction(snapAct)

    def SelectDevice(self):
        self.ic.LiveStop()
        self.ic.ShowDeviceSettingsDialog()
        if self.ic.DeviceValid is True:
            self.ic.LiveStart()
            self.ic.SaveDeviceStateToFile("device.xml")

    def ShowProperties(self):
        if self.ic.DeviceValid is True:
            self.ic.ShowPropertyDialog()
            self.ic.SaveDeviceStateToFile("device.xml")
    
    @pyqtSlot()
    def on_automode_btn_clicked(self):
        self.brain_focus.start()

    def gogo_run(self, image, laplacian_value):
        # test func
        self.__test__send("G28 Y0")
        
    @pyqtSlot()
    def on_machine_home_btn_clicked(self):
        self.__test__send("G28 Y0")
        self.__test__send("G91")
        self.__test__send("G1 Y20 F500")
        self.__test__send("G90")
        self.__test__send("M114")

    @pyqtSlot()
    def on_test_focus_btn_clicked(self):
        if self._serial_context_.isRunning():
            self._serial_context_.close()
        else:
            try:
                port = "COM4"
                baud = 115200
                self._serial_context_ = SerialPortContext(port=port, baud=baud)
                self._serial_context_.recall()
                self._serial_context_.registerReceivedCallback(self.__data_received__)
                self._serial_context_.open()
                self.test.get_serial_handle(self._serial_context_)
                # start the the button
                self._serial_button_Setting()
                self.run_servo.setEnabled(True)
                self.servo_slider.setEnabled(True)
            except :
                pass
                # QMessageBox.critical(self, f"error", u"can't open the comport,please check!")

        # time.sleep(2)
        # unlock the machine
        # self.__test__send("$X")  # unlock the machine

    def __test__send(self, data1):
        data = str(data1 + '\n')
        if self._serial_context_.isRunning():
            if len(data) > 0:
                print(data)
                self._serial_context_.send(data, 0)

    def __data_received__(self, data):
        self._receive_signal.emit(data)
        for c in range(len(data)):
            self.textEditReceived2.insertPlainText(data[c])
            sb = self.textEditReceived2.verticalScrollBar()
            sb.setValue(sb.maximum())

    def SnapImage(self):
        '''
        Snap and save an image
        '''
        image = self.snapsink.SnapSingle(TimeSpan.FromSeconds(1))
        TIS.Imaging.FrameExtensions.SaveAsBitmap(image, "test.bmp")

    # @pyqtSlot()
    # def on_check_btn_clicked(self):
    #     self.qti = QTimer()
    #     self.qti.timeout.connect(self.aaa)
    #     self.qti.start(500)

    @pyqtSlot()
    def on_run_servo_clicked(self):
        value = self.servo_spin.value()
        self.__test__send(f"M280 P0 S{value}")

    def sldDisconnect(self):
        self.sender().valueChanged.disconnect()

    def sldReconnect(self):
        self.sender().valueChanged.connect(self.sliderChanged)
        self.sender().valueChanged.emit(self.sender().value())

    def sliderChanged(self):
        # print(self.sender().objectName() + " : " + str(self.sender().value()))
        self.servo_spin.setValue(self.sender().value())
        self.__test__send(f"M280 P0 S{self.sender().value()}")

    # def aaa(self):
    #     self.__test__send("?")

    def closeEvent(self, event):
        self.flag = False
        if self.ic.DeviceValid is True:
            self.ic.LiveStop()

        self._is_auto_sending = False
        if self._serial_context_.isRunning():
            self._serial_context_.close()

    def imageCallback(self, x, y, buffer):
        print("hallo")
        return 0

    def OnDisplay(self, dispBuffer):
        copy = dispBuffer.pixmap.scaledToHeight(360)
        self.image1.setPixmap(copy)
        self.test_pixmap.emit(dispBuffer)
        dispBuffer.locked = False

    # entropy函数计算
    def entropy(self, img):
        '''
        :param img:narray 二维灰度图像
        :return: float 图像越清晰越大
        '''
        out = 0
        count = np.shape(img)[0]*np.shape(img)[1]
        p = np.bincount(np.array(img).flatten())
        for i in range(0, len(p)):
            if p[i] != 0:
                out -= p[i]*math.log(p[i]/count)/count
        return out
