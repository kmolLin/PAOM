# -*- coding: utf-8 -*-
import cv2
import numpy as np
import clr

path_dll = "C:/Users/smpss/Documents/IC Imaging Control 3.5/redist/dotnet/x64/TIS.Imaging.ICImagingControl35.dll"
if __name__ == '__main__':

    clr.AddReference(f"{path_dll}")
    
    from TIS.Imaging import ICImagingControl
    
    ic = ICImagingControl()
    
    ic.LiveDisplay = True
    
    # ic.ShowDeviceSettingsDialog()
    
    Devices = ic.Devices
    print(Devices)
    exit()
    
    for i in range(len(Devices)):
        print(f"find the device name {Devices[i]}")
    print(Devices)
    exit()
    if ic.DeviceValid == True:
        ic.LiveStart()
        
        ic.MemorySnapImage()
        
        ic.ImageActiveBuffer.SaveAsBitmap("camera.bmp")
        
        ic.LiveStop()
        
        print("Image save")
    




