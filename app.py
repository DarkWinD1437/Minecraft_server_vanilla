from __future__ import annotations

from textual.app import App

from mc_manager.__about__ import __brand__, __version__
from mc_manager.screens.main_screen import MainScreen
from mc_manager.screens.startup_screen import StartupScreen


class MCManager(App):
    """Minecraft Server Manager — Terminal UI."""

    TITLE = "MC Server Manager"
    SUB_TITLE = f"{__brand__}  v{__version__}"

    CSS_PATH = [
        "mc_manager/styles/main.tcss",
        "mc_manager/styles/common.tcss",
        "mc_manager/styles/monitoring.tcss",
    ]

    def on_mount(self) -> None:
        self.push_screen(MainScreen())
        self.push_screen(StartupScreen())


if __name__ == "__main__":
    MCManager().run()
