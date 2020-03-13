from pyvirtualdisplay.abstractdisplay import AbstractDisplay
from pyvirtualdisplay.xephyr import XephyrDisplay
from pyvirtualdisplay.xvfb import XvfbDisplay
from pyvirtualdisplay.xvnc import XvncDisplay
import fnmatch
import logging
import os
import select
import tempfile
import time
from threading import Lock

from easyprocess import EasyProcess, EasyProcessError

from pyvirtualdisplay import xauth

log = logging.getLogger(__name__)


X_START_TIMEOUT = 10
X_START_TIME_STEP = 0.1
X_START_WAIT = 0.1


class XStartTimeoutError(Exception):
    pass


class XStartError(Exception):
    pass


class Display(AbstractDisplay):
    """
    Common class

    :param color_depth: [8, 16, 24, 32]
    :param size: screen size (width,height)
    :param bgcolor: background color ['black' or 'white']
    :param visible: True -> Xephyr, False -> Xvfb
    :param backend: 'xvfb', 'xvnc' or 'xephyr', ignores ``visible``
    :param xauth: If a Xauthority file should be created.
    """

    def __init__(
        self,
        backend=None,
        visible=False,
        size=(1024, 768),
        color_depth=24,
        bgcolor="black",
        use_xauth=False,
        check_startup=False,
        randomizer=None,
        **kwargs
    ):
        self.color_depth = color_depth
        self.size = size
        self.bgcolor = bgcolor
        self.screen = 0
        self.process = None
        self.display = None
        self.visible = visible
        self.backend = backend

        if not self.backend:
            if self.visible:
                self.backend = "xephyr"
            else:
                self.backend = "xvfb"

        self._obj = self.display_class(
            size=size,
            color_depth=color_depth,
            bgcolor=bgcolor,
            randomizer=randomizer,
            **kwargs
        )
        AbstractDisplay.__init__(
            self,
            use_xauth=use_xauth,
            check_startup=check_startup,
            randomizer=randomizer,
        )

    # TODO: convert to property
    @property
    def display_class(self):
        assert self.backend
        if self.backend == "xvfb":
            cls = XvfbDisplay
        if self.backend == "xvnc":
            cls = XvncDisplay
        if self.backend == "xephyr":
            cls = XephyrDisplay

        # TODO: check only once
        cls.check_installed()

        return cls

    @property
    def _cmd(self):
        self._obj.display = self.display
        self._obj.check_startup = self.check_startup
        if self.check_startup:
            self._obj.check_startup_fd = self.check_startup_fd
        return self._obj._cmd

    def __enter__(self):
        """used by the :keyword:`with` statement"""
        self.start()
        return self

    def __exit__(self, *exc_info):
        """used by the :keyword:`with` statement"""
        self.stop()

    def is_alive(self):
        return self.proc.is_alive()

    @property
    def return_code(self):
        return self.proc.return_code

    def start(self):
        """
        start display

        :rtype: self
        """
        if self.use_xauth:
            self._setup_xauth()
        self.proc.start()
        time.sleep(0.01)

        # https://github.com/ponty/PyVirtualDisplay/issues/2
        # https://github.com/ponty/PyVirtualDisplay/issues/14
        self.old_display_var = os.environ.get("DISPLAY", None)

        self.redirect_display(True)

        # wait until X server is active
        start_time = time.time()
        if self.check_startup:
            rp = self._check_startup_fd
            display_check = None
            rlist, wlist, xlist = select.select((rp,), (), (), X_START_TIMEOUT)
            if rlist:
                display_check = os.read(rp, 10).rstrip()
            else:
                msg = "No display number returned by X server"
                raise XStartTimeoutError(msg)
            dnbs = str(self.display)
            if bytes != str:
                dnbs = bytes(dnbs, "ascii")
            if display_check != dnbs:
                msg = 'Display number "%s" not returned by X server' + str(
                    display_check
                )
                raise XStartTimeoutError(msg % self.display)

        d = self.new_display_var
        ok = False
        while True:
            if not self.proc.is_alive():
                break

            try:
                xdpyinfo = EasyProcess("xdpyinfo")
                xdpyinfo.enable_stdout_log = False
                xdpyinfo.enable_stderr_log = False
                exit_code = xdpyinfo.call().return_code
            except EasyProcessError:
                log.warning(
                    "xdpyinfo was not found, X start can not be checked! Please install xdpyinfo!"
                )
                time.sleep(X_START_WAIT)  # old method
                ok = True
                break

            if exit_code != 0:
                pass
            else:
                log.info('Successfully started X with display "%s".', d)
                ok = True
                break

            if time.time() - start_time >= X_START_TIMEOUT:
                break
            time.sleep(X_START_TIME_STEP)
        if not self.proc.is_alive():
            log.warning("process exited early",)
            msg = "Failed to start process: %s"
            raise XStartError(msg % self)
        if not ok:
            msg = 'Failed to start X on display "%s" (xdpyinfo check failed, stderr:[%s]).'
            raise XStartTimeoutError(msg % (d, xdpyinfo.stderr))
        return self

    def stop(self):
        """
        stop display

        :rtype: self
        """
        self.redirect_display(False)
        self.proc.stop()
        if self.use_xauth:
            self._clear_xauth()
        return self

    def _setup_xauth(self):
        """
        Set up the Xauthority file and the XAUTHORITY environment variable.
        """
        handle, filename = tempfile.mkstemp(
            prefix="PyVirtualDisplay.", suffix=".Xauthority"
        )
        self._xauth_filename = filename
        os.close(handle)
        # Save old environment
        self._old_xauth = {}
        self._old_xauth["AUTHFILE"] = os.getenv("AUTHFILE")
        self._old_xauth["XAUTHORITY"] = os.getenv("XAUTHORITY")

        os.environ["AUTHFILE"] = os.environ["XAUTHORITY"] = filename
        cookie = xauth.generate_mcookie()
        xauth.call("add", self.new_display_var, ".", cookie)

    def _clear_xauth(self):
        """
        Clear the Xauthority file and restore the environment variables.
        """
        os.remove(self._xauth_filename)
        for varname in ["AUTHFILE", "XAUTHORITY"]:
            if self._old_xauth[varname] is None:
                del os.environ[varname]
            else:
                os.environ[varname] = self._old_xauth[varname]
        self._old_xauth = None

    def redirect_display(self, on):
        """
        on:
         * True -> set $DISPLAY to virtual screen
         * False -> set $DISPLAY to original screen

        :param on: bool
        """
        d = self.new_display_var if on else self.old_display_var
        if d is None:
            log.debug("unset DISPLAY")
            del os.environ["DISPLAY"]
        else:
            log.debug("DISPLAY=%s", d)
            os.environ["DISPLAY"] = d
