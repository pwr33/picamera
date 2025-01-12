.. -*- rst -*-

========
pwr33/picamera
========

fork of picamera to test the MMALISPResizer and MMAL pipelines in python3 and do a proof of concept of fast multi resolution captures from the raspberry pi camera video port

If you want to test this, make sure you fork it and install it into a python3 virtual environment as there may well be some unidentified ramifications of having made the two simple changes to mmal.py and mmalobj.py

So as a result of a few days "scientifically" messing around with the ideosyncracies of MMAL, the proof of concept works and is provided here for anyone who wants to study it.

========
picamera
========

This package provides a pure Python interface to the `Raspberry Pi`_ `camera`_
module for Python 2.7 (or above) or Python 3.2 (or above).

Links
=====

* The code is licensed under the `BSD license`_
* The `source code`_ can be obtained from GitHub, which also hosts the `bug
  tracker`_
* The `documentation`_ (which includes installation, quick-start examples, and
  lots of code recipes) can be read on ReadTheDocs
* Packages can be downloaded from `PyPI`_, but reading the installation
  instructions is more likely to be useful


.. _Raspberry Pi: https://www.raspberrypi.org/
.. _camera: https://www.raspberrypi.org/learning/getting-started-with-picamera/
.. _PyPI: https://pypi.python.org/pypi/picamera/
.. _documentation: https://picamera.readthedocs.io/
.. _source code: https://github.com/waveform80/picamera
.. _bug tracker: https://github.com/waveform80/picamera/issues
.. _BSD license: https://opensource.org/licenses/BSD-3-Clause

