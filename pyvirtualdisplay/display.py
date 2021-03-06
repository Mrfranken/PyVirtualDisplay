from pyvirtualdisplay.abstractdisplay import AbstractDisplay
from pyvirtualdisplay.xephyr import XephyrDisplay
from pyvirtualdisplay.xvfb import XvfbDisplay
from pyvirtualdisplay.xvnc import XvncDisplay


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
