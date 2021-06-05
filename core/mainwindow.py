# -*- coding: utf-8 -*-

__author__ = "Yu-Sheng Lin"
__copyright__ = "Copyright (C) 2016-2020"
__license__ = "AGPL"
__email__ = "pyquino@gmail.com"

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUi
from PyQt5.QtCore import pyqtSlot

import ctypes as C
import numpy as np
import cv2
import clr
import os
import math
import time
from PIL import Image

import TIS.Imaging
from System import TimeSpan


def converte_pixmap2array(dispBuffer):

    channels_count = 4
    dispBuffer.pixmap.save("test.jpg")
    image = dispBuffer.pixmap.toImage()
    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    size = image.size()
    s = image.bits().asstring(size.width() * size.height() * image.depth() // 8)  # format 0xffRRGGBB
    arr = np.fromstring(s, dtype=np.uint8).reshape((size.height(), size.width(), image.depth() // 8))
    R, G, B, D = cv2.split(arr)
    BGR_image = cv2.merge([B, G, R])
    return BGR_image


class Thread_slect_focus(QThread):

    def __init__(self, send_thread_handle, parent=None):
        QThread.__init__(self, parent)
        self.send_thread = send_thread_handle
        self.image_arr = None
        self.laplacian = None

    def run(self):
        # while i < 20:
        step = 15
        self.send_thread.motion_step = [-20]
        self.send_thread.start()
        self.send_thread.wait()
        cnt = 0
        tmp = 0
        best_locate = 0
        while cnt < 15:
            cnt = cnt + 1
            self.send_thread.motion_step = [1]
            self.send_thread.start()
            self.send_thread.wait()
            if cnt == 1:
                tmp = self.laplacian
                continue

            if self.laplacian > tmp:
                tmp = self.laplacian
                best_locate = cnt

            if self.laplacian < tmp:
                self.send_thread.motion_step = [-1]
                self.send_thread.start()
                self.send_thread.wait()
                print(cnt)
                break

            time.sleep(0.1)

    def ttt(self, pixmap):
        self.image_arr = converte_pixmap2array(pixmap)

    def get_laplacin_value(self, image, laplacian):
        print(laplacian)
        self.laplacian = laplacian


class Thread_wait_forController(QThread):
    lnc_signal = pyqtSignal(int)
    laplacian_signal = pyqtSignal(object, object)

    def __init__(self, folder, parent=None):
        QThread.__init__(self, parent)
        self.folder = folder
        self.flag = True
        self.t0 = 0
        self.image_arr = None
        self.motion_step = None

    def run(self):
        i = 0
        while i < len(self.motion_step):

            f = open(f"{self.folder}/START", "w")
            f.close()
            f = open(f'{self.folder}/data.txt', 'w')
            f.write(f"{self.motion_step[i]}")
            f.close()
            while True:
                if os.path.isfile(f'{self.folder}/END'):
                    os.remove(f'{self.folder}/END')
                    self.laplacian_signal.emit(self.image_arr, self.Laplacina(self.image_arr))
                    break
                time.sleep(0.5)
            time.sleep(1)
            i += 1

    def motion(self, motion1: list):
        self.motion_step = motion1

    def ttt(self, pixmap):
        self.image_arr = converte_pixmap2array(pixmap)
        # print(pixmap)

    def Laplacina(self, img):
        return cv2.Laplacian(img, cv2.CV_64F).var()


class SinkData:
    brightnes = 0
    FrameBuffer = None


class DisplayBuffer:
    '''
    This class is needed to copy the image into a pixmap for
    displaying in the video window.
    '''
    locked = False
    pixmap = None
    img = None

    def Copy(self, FrameBuffer):
        if (int(FrameBuffer.FrameType.BitsPerPixel / 8) == 4):
            imgcontent = C.cast(FrameBuffer.GetIntPtr().ToInt64(),
                                C.POINTER(C.c_ubyte * FrameBuffer.FrameType.BufferSize))
            qimage = QImage(imgcontent.contents, FrameBuffer.FrameType.Width, FrameBuffer.FrameType.Height,
                            QImage.Format_RGB32).mirrored()
            self.img = qimage
            self.pixmap = QPixmap(qimage)


class WorkerSignals(QObject):
    display = pyqtSignal(object)


class DisplayFilter(TIS.Imaging.FrameFilterImpl):
    '''
    This frame filter copies an incoming frame into our
    DisplayBuffer object and signals the QApplication
    with the new buffer.
    '''
    __namespace__ = "DisplayFilterClass"
    signals = WorkerSignals()
    dispBuffer = DisplayBuffer()

    def GetSupportedInputTypes(self, frameTypes):
        frameTypes.Add(TIS.Imaging.FrameType(TIS.Imaging.MediaSubtypes.RGB32))

    def GetTransformOutputTypes(self, inType, outTypes):
        outTypes.Add(inType)
        return True

    def Transform(self, src, dest):
        dest.CopyFrom(src)
        if self.dispBuffer.locked is False:
            self.dispBuffer.locked = True
            self.dispBuffer.Copy(dest)
            self.signals.display.emit(self.dispBuffer)

        return False


class MainWindow(QMainWindow):

    test_pixmap = pyqtSignal(object)
    
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

        try:
            self.ic.LoadDeviceStateFromFile("device.xml", True)
            if self.ic.DeviceValid is True:
                self.ic.LiveStart()
        except Exception as ex:
            print(ex)
            pass

        # Connect the display signal handler to our filter.
        # self.image1

    def finff(self):
        print("finished")

    def __init_setting(self):
        # Load IC Imaging Control .NET
        # Import the IC Imaging Control namespace.
        pass

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
        # motion = [1.0] * 26
        # motion[0] = -25.0
        # self.test.motion_step = [-5]
        # self.test.start()
        # self.test.wait()
        # for i in [1, 1, 1, 1, 1]:
        #     self.test.motion_step = [i]
        #     self.test.start()
        #     self.test.wait()

    def gogo_run(self, image, laplacian_value):
        # test func
        print(laplacian_value)
        # f = open("clear_fy.txt", "a+")
        # f.write(f"{laplacian_value}\n")
        # f.close()
        # cv2.imwrite(f"tmp_img/{self.count}.jpg", image)
        # self.laplacian_label.setText(f"{laplacian_value}")
        # self.count += 1

    @pyqtSlot()
    def on_test_focus_btn_clicked(self):
        print("test")

    def SnapImage(self):
        '''
        Snap and save an image
        '''
        image = self.snapsink.SnapSingle(TimeSpan.FromSeconds(1))
        TIS.Imaging.FrameExtensions.SaveAsBitmap(image, "test.bmp")

    def closeEvent(self, event):
        self.flag = False
        if self.ic.DeviceValid is True:
            self.ic.LiveStop()
        # self.quit()

    def imageCallback(self, x, y, buffer):
        print("hallo")
        return 0

    def OnDisplay(self, dispBuffer):
        copy = dispBuffer.pixmap.scaledToHeight(360)
        self.image1.setPixmap(copy)
        self.test_pixmap.emit(dispBuffer)
        # self.ndimage = self.QImageToCvMat(dispBuffer.img)
        # canny = cv2.Canny(self.ndimage, 30, 150)
        # size = (640, 512)
        # shrink = cv2.resize(canny, size, interpolation=cv2.INTER_AREA)
        # shrink = cv2.cvtColor(shrink, cv2.COLOR_BGR2RGB)
        # self.QtImg = QImage(shrink.data,
        #                           shrink.shape[1],
        #                           shrink.shape[0],
        #                           QImage.Format_RGB888)
        # self.image2.setPixmap(QPixmap.fromImage(self.QtImg))
        # text = self.Laplacina(cv2.cvtColor(self.ndimage, cv2.COLOR_BGR2GRAY))
        # print(dispBuffer.pixarray)
        # self.converte_pixmap2array()
        # self.laplacian_label.setText(f"{text}")
        dispBuffer.locked = False


    #entropy函数计算
    def entropy(self, img):
        '''
        :param img:narray 二维灰度图像
        :return: float 图像越清晰越大
        '''
        out = 0
        count = np.shape(img)[0]*np.shape(img)[1]
        p = np.bincount(np.array(img).flatten())
        for i in range(0, len(p)):
            if p[i]!=0:
                out-=p[i]*math.log(p[i]/count)/count
        return out
