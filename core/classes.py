# -*- coding: utf-8 -*-

__author__ = "Yu-Sheng Lin"
__copyright__ = "Copyright (C) 2016-2022"
__license__ = "AGPL"
__email__ = "pyquino@gmail.com"

import numpy as np
import cv2
import time
import os
import TIS.Imaging
import ctypes as C

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from System import TimeSpan
from core.serial_core.serialportcontext import SerialPortContext


def converte_pixmap2array(dispBuffer):

    channels_count = 4
    # dispBuffer.pixmap.save("test.jpg")
    image = dispBuffer.pixmap.toImage()
    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    size = image.size()
    s = image.bits().asstring(size.width() * size.height() * image.depth() // 8)  # format 0xffRRGGBB
    arr = np.fromstring(s, dtype=np.uint8).reshape((size.height(), size.width(), image.depth() // 8))
    R, G, B, D = cv2.split(arr)
    BGR_image = cv2.merge([B, G, R])
    return BGR_image


def conver_qimage2array(img: QImage):

    image = img.convertToFormat(QImage.Format.Format_RGBA8888)
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
        # self.send_thread.motion_step = [-15]
        # self.send_thread.start()
        # self.send_thread.wait()
        cnt = 0
        tmp = 0
        best_locate = 0
        tmp = []
        while cnt < 15:

            self.send_thread.motion_step = [10]
            self.send_thread.start()
            self.send_thread.wait()
            tmp.append(self.laplacian)
            cnt = cnt + 1

            self.msleep(100)
        # self.send_thread.motion_step = [tmp.index(max(tmp)) - 15]
        # self.send_thread.start()
        # self.send_thread.wait()

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
        self.serial_hadle = None
        self.status_flag = False
        self.staMode = False

    def run(self):
        i = 0
        if self.serial_hadle.isRunning():
            while i < len(self.motion_step):
                self.ramps_command(self.motion_step[i])
                # text = f"$J=G21G91Y{self.motion_step[i]}F250"                
                # self.__test__send(self.serial_hadle, f"{text}")  # this line is command
                # self.__test__send(self.serial_hadle, "M114")
                while True:
                    if self.status_flag:
                        self.laplacian_signal.emit(self.image_arr, self.Laplacina(self.image_arr))
                        break
                    else:
                        self.msleep(500)
                self.msleep(200)
                self.status_flag = False
                self.staMode = False
                i += 1
    
    def ramps_command(self, move_distance):
        self.__test__send(self.serial_hadle, "G91")
        self.__test__send(self.serial_hadle, f"G1 Y{move_distance} F500")
        self.__test__send(self.serial_hadle, "G90")
        self.__test__send(self.serial_hadle, "M114")
        self.staMode = True

    def __test__send(self, contex, data1):
        data = str(data1 + '\n')
        if contex.isRunning():
            if len(data) > 0:
                contex.send(data, 0)

    def test_received(self, data):
        if data.startswith("echo:busy") or self.staMode:
            print(data)
            if data.startswith("X:"):
                print(data)
                # x, y, z = data.split("|")[1].split(":")[1].split(",")
                # print(f"X:{x} Y:{y} Z:{z}")
                self.status_flag = True

        elif data.startswith("<Run|"):
            pass

    def aaa(self):
        self.__test__send(self.serial_hadle, "?")

    def motion(self, motion1: list):
        self.motion_step = motion1

    def get_serial_handle(self, serial_handle):
        self.serial_hadle = serial_handle

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