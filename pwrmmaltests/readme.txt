Proof of concept - fast-ish multi resolution capture from Raspberry Pi camera video port using an mmal pipeline in python3

Well, this example points you in the right direction, however you will need to change the callbacks that write to memory buffers to use a bytesarray and do a bytesarray.extend(buf.data) instead of my initial naive, value = buf.data.

Having done that the preview works fine running at same time, and is a fast loop and getting good exposures now!

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
