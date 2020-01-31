from unittest import TestCase

from easyprocess import EasyProcess
from nose.tools import eq_

from pyvirtualdisplay.smartdisplay import SmartDisplay

# from path import path
# import pyscreenshot


class Test(TestCase):
    def test_double(self):
        with SmartDisplay(visible=0, bgcolor="black") as disp:
            with EasyProcess("xmessage hello1"):
                img = disp.waitgrab()
                eq_(img is not None, True)

        with SmartDisplay(visible=0, bgcolor="black") as disp:
            with EasyProcess("xmessage hello2"):
                img = disp.waitgrab()
                eq_(img is not None, True)
