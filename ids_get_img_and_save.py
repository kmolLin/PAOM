from ctypes import *
from pyueye import ueye
import numpy as np
import cv2
import sys
import ctypes
import struct
import threading
import queue
import time
#---------------------------------------------------------------------------------------------------------------------------------------

#Variables

save_path = "C:/Users/smpss/kmol/IDS_camera/backlight_exoeriment/save_experiment0711"
time_exposure_ = 29.9 # (my thoughts, not original to the post.  I think this represents 3 milliseconds, but I'm not sure?
gains = 0
time_exposure = ueye.double(time_exposure_)

hCam = ueye.HIDS(0)             #0: first available camera;  1-254: The camera with the specified camera ID
sInfo = ueye.SENSORINFO()
cInfo = ueye.CAMINFO()
pcImageMemory = ueye.c_mem_p()
MemID = ueye.int()
rectAOI = ueye.IS_RECT()
pitch = ueye.INT()
nBitsPerPixel = ueye.INT(24)    #24: bits per pixel for color mode; take 8 bits per pixel for monochrome
channels = 3                    #3: channels for color mode(RGB); take 1 channel for monochrome
m_nColorMode = ueye.INT()		# Y8/RGB16/RGB24/REG32
bytes_per_pixel = int(nBitsPerPixel / 8)
now=ctypes.c_uint()
#=ueye.UEYE_AUTO_INFO()

#---------------------------------------------------------------------------------------------------------------------------------------
print("START")
print()


# Starts the driver and establishes the connection to the camera
nRet = ueye.is_InitCamera(hCam, None)
if nRet != ueye.IS_SUCCESS:
    print("is_InitCamera ERROR")

# Reads out the data hard-coded in the non-volatile camera memory and writes it to the data structure that cInfo points to
nRet = ueye.is_GetCameraInfo(hCam, cInfo)
if nRet != ueye.IS_SUCCESS:
    print("is_GetCameraInfo ERROR")

# You can query additional information about the sensor type used in the camera
nRet = ueye.is_GetSensorInfo(hCam, sInfo)
if nRet != ueye.IS_SUCCESS:
    print("is_GetSensorInfo ERROR")

nRet = ueye.is_ResetToDefault( hCam)
if nRet != ueye.IS_SUCCESS:
    print("is_ResetToDefault ERROR")



# Set display mode to DIB
nRet = ueye.is_SetDisplayMode(hCam, ueye.IS_SET_DM_DIB)

# Set the right color mode
if int.from_bytes(sInfo.nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_BAYER:
    # setup the color depth to the current windows setting
    ueye.is_GetColorDepth(hCam, nBitsPerPixel, m_nColorMode)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print("IS_COLORMODE_BAYER: ", )
    print("\tm_nColorMode: \t\t", m_nColorMode)
    print("\tnBitsPerPixel: \t\t", nBitsPerPixel)
    print("\tbytes_per_pixel: \t\t", bytes_per_pixel)
    print()

elif int.from_bytes(sInfo.nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_CBYCRY:
    # for color camera models use RGB32 mode
  
    nBitsPerPixel = ueye.INT(32)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print("IS_COLORMODE_CBYCRY: ", )
    print("\tm_nColorMode: \t\t", m_nColorMode)
    print("\tnBitsPerPixel: \t\t", nBitsPerPixel)
    print("\tbytes_per_pixel: \t\t", bytes_per_pixel)
    print()

elif int.from_bytes(sInfo.nColorMode.value, byteorder='big') == ueye.IS_COLORMODE_MONOCHROME:
    # for color camera models use RGB32 mode
    m_nColorMode = ueye.IS_CM_MONO8
    nBitsPerPixel = ueye.INT(8)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print("IS_COLORMODE_MONOCHROME: ", )
    print("\tm_nColorMode: \t\t", m_nColorMode)
    print("\tnBitsPerPixel: \t\t", nBitsPerPixel)
    print("\tbytes_per_pixel: \t\t", bytes_per_pixel)
    print()

else:
    # for monochrome camera models use Y8 mode
    m_nColorMode = ueye.IS_CM_MONO8
    nBitsPerPixel = ueye.INT(8)
    bytes_per_pixel = int(nBitsPerPixel / 8)
    print("else")

# Can be used to set the size and position of an "area of interest"(AOI) within an image
nRet = ueye.is_AOI(hCam, ueye.IS_AOI_IMAGE_GET_AOI, rectAOI, ueye.sizeof(rectAOI))
if nRet != ueye.IS_SUCCESS:
    print("is_AOI ERROR")

width =rectAOI.s32Width
height =rectAOI.s32Height

# Prints out some information about the camera and the sensor
print("Camera model:\t\t", sInfo.strSensorName.decode('utf-8'))
print("Camera serial no.:\t", cInfo.SerNo.decode('utf-8'))
print("Maximum image width:\t", width)
print("Maximum image height:\t", height)
print()

#---------------------------------------------------------------------------------------------------------------------------------------

# Allocates an image memory for an image having its dimensions defined by width and height and its color depth defined by nBitsPerPixel
nRet = ueye.is_AllocImageMem(hCam, width, height, nBitsPerPixel, pcImageMemory, MemID)
if nRet != ueye.IS_SUCCESS:
    print("is_AllocImageMem ERROR")
else:
    # Makes the specified image memory the active memory
    nRet = ueye.is_SetImageMem(hCam, pcImageMemory, MemID)
    if nRet != ueye.IS_SUCCESS:
        print("is_SetImageMem ERROR")
    else:
        # Set the desired color mode
        print(m_nColorMode)
        nRet = ueye.is_SetColorMode(hCam, m_nColorMode)


nRet = ueye.is_Exposure(hCam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE, time_exposure, ueye.sizeof(time_exposure))
print(nRet)
gain_value = int(gains)
# nRet = ueye.is_SetHWGainFactor(hCam, ueye.IS_SET_MASTER_GAIN_FACTOR, gain_value)
# print(nRet)
real_fps = ueye.DOUBLE()
ueye.is_SetFrameRate(hCam, 33.0, real_fps)

print(real_fps)
# Activates the camera's live video mode (free run mode)
nRet = ueye.is_CaptureVideo(hCam, ueye.IS_DONT_WAIT)
if nRet != ueye.IS_SUCCESS:
    print("is_CaptureVideo ERROR")

nRet = ueye.is_InquireImageMem(hCam, pcImageMemory, MemID, width, height, nBitsPerPixel, pitch)
if nRet != ueye.IS_SUCCESS:
    print("is_InquireImageMem ERROR")
else:
    print("Press q to leave the programm")

init_events = ueye.IS_INIT_EVENT()
init_events.nEvent=ueye.IS_SET_EVENT_FRAME
init_events.bManualReset=False
init_events.bInitialState=False
ueye.is_Event(hCam, ueye.IS_EVENT_CMD_INIT, init_events, ueye.sizeof(init_events))

events=ueye.c_uint(ueye.IS_SET_EVENT_FRAME)
ueye.is_Event(hCam, ueye.IS_EVENT_CMD_ENABLE, events, ueye.sizeof(events))

wait_events = ueye.IS_WAIT_EVENT()
wait_events.nEvent = ueye.IS_SET_EVENT_FRAME
wait_events.nCount = 2
wait_events.nTimeoutMilliseconds = 1000
wait_events.nSignaled = 0
wait_events.nSetCount = 0

tmp = []
cv2.namedWindow("SimpleLive_Python_uEye_OpenCV", cv2.WINDOW_NORMAL)

# 用于存储照片的队列
photo_queue = queue.Queue()

# 线程函数，用于处理照片的储存
def process_photos():
    while True:
        # 从队列中获取照片
        datas = photo_queue.get()

        # 假设这里是将照片存储到文件系统中以及 index
        save_photo_to_file(datas)

        # 标记照片任务完成
        photo_queue.task_done()

# 假设这是保存照片到文件系统的函数
def save_photo_to_file(datas):
    # 执行照片的储存操作
    cv2.imwrite(f"{save_path}/{datas[1]:02d}.jpg", datas[0])
    
# 创建并启动照片处理线程
photo_thread = threading.Thread(target=process_photos)
photo_thread.daemon = True  # 设置线程为守护线程，即主线程退出时自动退出子线程
photo_thread.start()

count = 0

while(nRet == ueye.IS_SUCCESS):

    ret = ueye.is_Event(hCam, ueye.IS_EVENT_CMD_WAIT, wait_events, ueye.sizeof(wait_events))

    if (ueye.IS_SET_EVENT_FRAME == wait_events.nSignaled):    
        # Continuous image display
        # In order to display the image in an OpenCV window we need to...
        # ...extract the data of our image memory
        array = ueye.get_data(pcImageMemory, width, height, nBitsPerPixel, pitch, copy=True) 
        # bytes_per_pixel = int(nBitsPerPixel / 8) 
        # ...reshape it in an numpy array...
        frame = np.reshape(array,(height.value, width.value, bytes_per_pixel))
        #nRet = ueye.is_ImageFile(hCam, ueye.IS_IMAGE_FILE_CMD_SAVE, ImageFileParams, ueye.sizeof(ImageFileParams))
        photo_queue.put([frame, count])
        # frame = cv2.resize(frame,(0,0),fx=0.5, fy=0.5)

        count = count + 1
        cv2.imshow("SimpleLive_Python_uEye_OpenCV", frame)
    if count > 1000:
        break
    # Press q if you want to end the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
#---------------------------------------------------------------------------------------------------------------------------------------
# Releases an image memory that was allocated using is_AllocImageMem() and removes it from the driver management
ueye.is_FreeImageMem(hCam, pcImageMemory, MemID)

# Disables the hCam camera handle and releases the data structures and memory areas taken up by the uEye camera
ueye.is_ExitCamera(hCam)

# Destroys the OpenCv windows
cv2.destroyAllWindows()

print()
print("END")
