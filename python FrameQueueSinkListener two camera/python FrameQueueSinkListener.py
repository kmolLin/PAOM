

import ctypes as C
import numpy as np
import cv2
import time as time
# Import PyhtonNet
import clr
from datetime import datetime
# Load IC Imaging Control .NET 
clr.AddReference('TIS.Imaging.ICImagingControl35')
clr.AddReference('System')

# Import the IC Imaging Control namespace.
import TIS.Imaging
from System import TimeSpan
from TIS.Imaging import VCDGUIDs, MediaSubtypes

# create a listener for the sink
class Listener(TIS.Imaging.IFrameQueueSinkListener):
    pass

    # do other stuff with that frame
    # input parameters of the methods are built to match what it is provided
    __namespace__ = 'ListenerNameSpace'
    #frametype = TIS.Imaging.FrameType(TIS.Imaging.MediaSubtypes.Y800)

    def SinkConnected(self, sink, frameType ):
        print('Sink connected')
        sink.AllocAndQueueBuffers(20)
    
    def SinkDisconnected(self, sink,buffers):
        print('Sink disconnected')

    def FramesQueued(self,  sink):
        frame = sink.PopAllOutputQueueBuffers()
        for val in frame:
            # TIS.Imaging.FrameExtensions.SaveAsJpeg(frame,"test.jpg",75)
            imgcontent = C.cast(val.GetIntPtr().ToInt64(), C.POINTER(C.c_ubyte * val.FrameType.BufferSize))
            img = np.ndarray(buffer = imgcontent.contents,
                            dtype = np.uint8,
                            shape = (val.FrameType.Height,
                            val.FrameType.Width,
                            int(val.FrameType.BitsPerPixel/8 )) )
            cv2.flip( img,0,img )
            #cv2.imwrite('testtt.jpg',img)
            cv2.imshow('camera1',img)
            cv2.waitKey(1)
            sink.QueueBuffer(val)




# Create the IC Imaging Control object.
ic = TIS.Imaging.ICImagingControl()

listener = Listener(TIS.Imaging.IFrameQueueSinkListener)
sink = TIS.Imaging.FrameQueueSink(listener,MediaSubtypes.RGB24)

ic.Sink = sink
#ic.ShowDeviceSettingsDialog()
#ic.SaveDeviceStateToFile("device.xml")
ic.LoadDeviceStateFromFile("device.xml", True)


ic.LiveStart()



time.sleep(10)

ic.LiveStop()

