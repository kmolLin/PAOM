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