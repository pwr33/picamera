#!/usr/bin/python3
# a class to test picamera at mmal level
# very specific functionality - provide 1 pipeline that is exactly what I want and blit functions
# use video port as its faster
# on a pi zero cam port is about 0.5 seconds a shot, vid about .1 a shot (at 10 fps)
#
# test my required pipeline of:  cam - splitter - resizer - encoders
#
# structured enough to make itself somewhat reusable/hackable I think.
# And serve as a reasonable example
# 
#
# Author Paul W. Rogers 2021
# copyright (c) 2021 Paul W. Rogers


from picamera import mmal, mmalobj as mo
from threading import Event
import time
import traceback
from datetime import datetime
from PIL import Image
import numpy as np

# pass in an x,y tuple
def mmalbufsize(size) :
  # calculate the rounded capture size
  fwidth = (size[0] + 31) // 32 * 32 
  fheight = (size[1] + 15) // 16 * 16
  return (fwidth,fheight)

class pwrmmalcam() :
    
  def __init__(self,size=(1296,972),framerate=10) :
    self.size = size
    self.framerate = framerate
    self.inittime = time.time()
    self.cam = mo.MMALCamera()
    self.preview = mo.MMALRenderer()
    self.nullpreview = mo.MMALNullSink()
    self.encodersmall = mo.MMALImageEncoder()
    self.encoderlarge = mo.MMALImageEncoder()
    self.ispresizer = mo.MMALISPResizer()
    self.splitter = mo.MMALSplitter()
    # variables for splitter - encoder and ISPresizer pipeline
    # may want to capture jpegs to a memory buffer or a file
    self.ispresizerlargesize = (640,480)
    self.ispresizersmallsize = (128,80)
    self.encoderlargebuf = None
    self.encodersmallbuf = None
    self.ispresizersmallbuf = None
    self.encoderlargefn = None
    self.encodersmallfn = None
    self.encoderlargefile = None
    self.encodersmallfile = None
    self.encoderlarge_finished = Event()
    self.encodersmall_finished = Event()
    self.ispresizersmall_finished = Event()

  # initialise the pipeline for video port chain  
  # allow components to choose their own format on the connect
  # then will use OPQV as far down the chains as required
  # unless you want I422 then specify that output on the cam port I think
  # little subtleties I have not yet fully tested
  def initpipeline(self,port=1) :
    # init cam output port
    self.cam.outputs[port].format = mmal.MMAL_ENCODING_OPAQUE
    self.cam.outputs[port].framesize = self.size
    self.cam.outputs[port].framerate = self.framerate
    self.cam.outputs[port].commit()
    # init splitter using ports 0 and 1
    self.splitter.inputs[0].format = mmal.MMAL_ENCODING_OPAQUE
    #self.splitter.outputs[0].format = mmal.MMAL_ENCODING_I422
    self.splitter.outputs[0].commit()
    #self.splitter.outputs[1].format = mmal.MMAL_ENCODING_I422
    self.splitter.outputs[1].commit()

    # init resizer to be connected to splitter 1
    #self.ispresizer.inputs[0].format = mmal.MMAL_ENCODING_I422
    self.ispresizer.outputs[0].framesize = self.ispresizerlargesize
    #self.ispresizer.outputs[0].format = mmal.MMAL_ENCODING_I422
    self.ispresizer.outputs[0].commit()         
    self.ispresizer.outputs[1].framesize = self.ispresizersmallsize
    # only going to use the Y channel of the test image so can be smaller I420
    # set this format as it defaults to yuyv in my tests
    self.ispresizer.outputs[1].format = mmal.MMAL_ENCODING_I420
    self.ispresizer.outputs[1].commit()         

    # init large encoder to be connected to splitter 0
    #self.encoderlarge.inputs[0].format = mmal.MMAL_ENCODING_I422
    self.encoderlarge.outputs[0].framesize = self.size
    self.encoderlarge.outputs[0].format = mmal.MMAL_ENCODING_JPEG
    self.encoderlarge.outputs[0].params[mmal.MMAL_PARAMETER_JPEG_Q_FACTOR] = 15
    self.encoderlarge.outputs[0].commit()         
    
    # init small encoder to connect to resizer 0
    #self.encodersmall.inputs[0].format = mmal.MMAL_ENCODING_I422
    self.encodersmall.outputs[0].framesize = self.ispresizerlargesize
    self.encodersmall.outputs[0].format = mmal.MMAL_ENCODING_JPEG
    self.encodersmall.outputs[0].params[mmal.MMAL_PARAMETER_JPEG_Q_FACTOR] = 15
    self.encodersmall.outputs[0].commit()         
    
    # connect ports 
    self.splitter.connect(self.cam.outputs[port])
    self.splitter.connection.enable()

    self.encoderlarge.connect(self.splitter.outputs[0])   
    self.encoderlarge.connection.enable()
    mo.print_pipeline(self.encoderlarge.outputs[0]) 
        
    self.ispresizer.connect(self.splitter.outputs[1])   
    self.ispresizer.connection.enable()
    
    self.encodersmall.connect(self.ispresizer.outputs[0])   
    self.encodersmall.connection.enable()
    print("=" * 70)
    mo.print_pipeline(self.encodersmall.outputs[0]) 
    print("=" * 70)
    mo.print_pipeline(self.ispresizer.outputs[1])     
  
  # blit data from cam to stored jpegs and a small memory buffer
  def blitfile(self,port=1) :
    self.encoder_largefn = "/home/pi/mmaltests/enclarge_{}.jpg".format(datetime.now().isoformat(timespec='microseconds'))
    self.encoder_smallfn = "/home/pi/mmaltests/encsmall_{}.jpg".format(datetime.now().isoformat(timespec='microseconds'))
    self.encoderlargefile = open(self.encoder_largefn, 'wb')
    self.encodersmallfile = open(self.encoder_smallfn, 'wb')
    self.encoderlarge_finished.clear()
    self.encodersmall_finished.clear()
    self.ispresizersmall_finished.clear()
    
    self.encoderlarge.outputs[0].enable(self.encoderlarge_file_callback)
    self.encodersmall.outputs[0].enable(self.encodersmall_file_callback)
    self.ispresizer.outputs[1].enable(self.ispresizersmall_callback)
     
    self.cam.outputs[port].params[mmal.MMAL_PARAMETER_CAPTURE] = True

    # simple sequential wait on all events 
    if not self.encoderlarge_finished.wait(2):
      raise Exception('encoder large capture timed out')
    if not self.encodersmall_finished.wait(1):
      raise Exception('encoder small capture timed out')
    if not self.ispresizersmall_finished.wait(1):
      raise Exception('encoder small capture timed out')

    self.cam.outputs[port].params[mmal.MMAL_PARAMETER_CAPTURE] = False
    
    self.encoderlarge.outputs[0].disable()
    self.encodersmall.outputs[0].disable()
    self.ispresizer.outputs[1].disable()
    
    self.encoderlargefile.close()
    self.encodersmallfile.close()
    
  # blit data to memory buffers
  def blitbuffer(self,port=1) :
    self.encoderlarge_finished.clear()
    self.encodersmall_finished.clear()
    self.ispresizersmall_finished.clear()

    self.encoderlarge.outputs[0].enable(self.encoderlarge_buffer_callback)
    self.encodersmall.outputs[0].enable(self.encodersmall_buffer_callback)
    self.ispresizer.outputs[1].enable(self.ispresizersmall_callback)

    self.cam.outputs[port].params[mmal.MMAL_PARAMETER_CAPTURE] = True

    # simple sequential wait on all events 
    if not self.encoderlarge_finished.wait(10):
      raise Exception('encoder large capture timed out')
    if not self.encodersmall_finished.wait(1):
      raise Exception('encoder small capture timed out')
    if not self.ispresizersmall_finished.wait(1):
      raise Exception('encoder small capture timed out')

    self.cam.outputs[port].params[mmal.MMAL_PARAMETER_CAPTURE] = False

    self.encoderlarge.outputs[0].disable()
    self.encodersmall.outputs[0].disable()
    self.ispresizer.outputs[1].disable()

  # output large image to file
  def encoderlarge_file_callback(self, port, buf):
      self.encoderlargefile.write(buf.data)
      if buf.flags & mmal.MMAL_BUFFER_HEADER_FLAG_FRAME_END:
        self.encoderlarge_finished.set()
        return True
      return False
    
  # output small image to file
  def encodersmall_file_callback(self, port, buf):
      self.encodersmallfile.write(buf.data)
      if buf.flags & mmal.MMAL_BUFFER_HEADER_FLAG_FRAME_END:
        self.encodersmall_finished.set()
        return True
      return False

  # output large image to buffer
  def encoderlarge_buffer_callback(self, port, buf):
      self.encoderlargebuf = buf.data
      if buf.flags & mmal.MMAL_BUFFER_HEADER_FLAG_FRAME_END:
        self.encoderlarge_finished.set()
        return True
      return False
    
  # output small image to buffer
  def encodersmall_buffer_callback(self, port, buf):
      self.encodersmallbuf = buf.data
      if buf.flags & mmal.MMAL_BUFFER_HEADER_FLAG_FRAME_END:
        self.encodersmall_finished.set()
        return True
      return False

  # copy the small resized image to a memory buffer
  def ispresizersmall_callback(self, port, buf):
      self.ispresizersmallbuf = buf.data
      if buf.flags & mmal.MMAL_BUFFER_HEADER_FLAG_FRAME_END:
        self.ispresizersmall_finished.set()
        return True
      return False
    
  def printinfo(self) :
    print("=" * 100,"CAMERA")
    print(self.cam.outputs)
    print("=" * 100,"PREVIEW")
    print(self.preview.inputs)
    print("=" * 100,"SPLITTER")
    print(self.splitter.inputs)
    print(self.splitter.outputs)
    print("=" * 100,"ISPRESIZER")
    print(self.ispresizer.inputs)
    print(self.ispresizer.outputs)    
 
  def startnullpreview(self) :
    self.cam.outputs[0].framerate = self.framerate
    self.cam.outputs[0].commit()
    self.nullpreview.inputs[0].connect(self.cam.outputs[0])
    self.nullpreview.connection.enable()

  def stopnullpreview(self) :
    self.nullpreview.connection.disable()
    self.nullpreview.inputs[0].disconnect()
   
  def startpreview(self) :
    self.cam.outputs[0].framerate = self.framerate
    self.cam.outputs[0].commit()
    self.preview.inputs[0].connect(self.cam.outputs[0])
    self.preview.connection.enable()

  def stoppreview(self) :
    self.preview.connection.disable()
    self.preview.inputs[0].disconnect()
        
    
  # python3 does a pretty good job of cleaning up after itself anyway nowadays eh!
  def shutdown(self) :
    #self.stoppreview()
    pass

if __name__=="__main__" :
  # 10fps seems about as fast as it can consistently do (but the test pi zero-w is running two other file outputters which flush buffers).
  # that is all I was aiming for, effectively twice as fast as throwing away a frame in my existing motion detection method
  # and also getting two jpegs (3 images) per frame
  # cam = pwrmmalcam(framerate=30)
  cam = pwrmmalcam()
  cam.printinfo()
  #cam.startnullpreview()
  cam.startpreview()
  wtime = 10
  print("Warmup ",wtime)
  time.sleep(wtime)
  # testing on a pi zero with a V1 pi camera it seems need to
  # stop the preview that is started If you want to run at a fast framerate
  # otherwise very unpredictable results can happen.... 
  # 
  #cam.stopnullpreview()
  cam.stoppreview()
  cam.initpipeline()
  
  loopst = time.perf_counter()
  for i in range(100) :
    st = time.perf_counter()
    cam.blitbuffer()
    # save a greyscale image from the test/tiny I420 buffer returned as well.
    img = Image.frombytes("L",cam.ispresizersmallsize,cam.ispresizersmallbuf)
    imgname = "/home/pi/mmaltests/xsmall{}.jpg".format(datetime.now().isoformat(timespec='microseconds'))
    img.save(imgname)
    print("took",time.perf_counter()-st)
  print("Loop took",time.perf_counter()-loopst)
  
  loopst = time.perf_counter()
  for i in range(100) :
    st = time.perf_counter()
    cam.blitfile()
    # save a greyscale image from the test/tiny I420 buffer returned as well.
    img = Image.frombytes("L",cam.ispresizersmallsize,cam.ispresizersmallbuf)
    imgname = "/home/pi/mmaltests/xsmall{}.jpg".format(datetime.now().isoformat(timespec='microseconds'))
    img.save(imgname)
    
    print("took",time.perf_counter()-st)
  print("Loop took",time.perf_counter()-loopst)
  
  #input("press any key")
