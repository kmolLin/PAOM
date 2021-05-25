# -*- coding: utf-8 -*-

import sys
import clr
import os
from PyQt5.QtWidgets import *


if __name__ == "__main__":
    t = os.path.dirname(os.path.abspath(__file__))
    path_dll = os.path.join(t, "core/dll/", "TIS.Imaging.ICImagingControl35.dll")
    clr.AddReference(f'{path_dll}')
    clr.AddReference('System')
    from core.mainwindow import MainWindow
    app = QApplication(sys.argv)
    window = MainWindow()
    app.exec_()
