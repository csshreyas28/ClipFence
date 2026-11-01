import pystray

from PIL import Image, ImageDraw


class ClipFenceTray:

    def __init__(
        self,
        on_show,
        on_toggle,
        on_pause,
        on_exit
    ):
        self.on_show = on_show
        self.on_toggle = on_toggle
        self.on_pause = on_pause
        self.on_exit = on_exit

        self.icon = pystray.Icon(
            "ClipFence",
            self._create_icon(),
            "ClipFence",
            menu=self._create_menu()
        )

    def _create_icon(self):
        image = Image.new(
            "RGB",
            (64, 64),
            "white"
        )

        draw = ImageDraw.Draw(image)

        draw.rounded_rectangle(
            (8, 8, 56, 56),
            radius=10,
            fill="black"
        )

        draw.text(
            (20, 18),
            "C",
            fill="white",
            font=None
        )

        return image

    def _create_menu(self):
        return pystray.Menu(
            pystray.MenuItem(
                "Open ClipFence",
                self._show
            ),
            pystray.MenuItem(
                "Toggle Protection",
                self._toggle
            ),
            pystray.MenuItem(
                "Pause 10 Minutes",
                self._pause
            ),
            pystray.MenuItem(
                "Exit",
                self._exit
            )
        )

    def _show(self, icon, item):
        self.on_show()

    def _toggle(self, icon, item):
        self.on_toggle()

    def _pause(self, icon, item):
        self.on_pause()

    def _exit(self, icon, item):
        self.on_exit()

    def run(self):
        self.icon.run()

    def stop(self):
        self.icon.stop()