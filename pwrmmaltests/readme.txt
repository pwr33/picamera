Proof of concept - fast-ish multi resolution capture from Raspberry Pi camera video port using an mmal pipeline in python3

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
