import os

from kivy.properties import StringProperty
from kivy.uix.modalview import ModalView
from kivy.utils import get_color_from_hex, get_hex_from_color

from kivymd.color_definitions import colors, palette
from kivymd.theming import ThemableBehavior

class ProjectBaseDialog(ThemableBehavior, ModalView):
    pass


class ProjectDialogDev(ProjectBaseDialog):
    pass


class ProjectUsageCode(ProjectBaseDialog):
    code = StringProperty()
    title = StringProperty()
    website = StringProperty()


class ProjectDialogLicense(ProjectBaseDialog):
    def on_open(self):
        with open(
            os.path.join(os.environ["PROJECT_ROOT"], "LICENSE"),
            encoding="utf-8",
        ) as license:
            self.ids.text_label.text = license.read().format(
                COLOR=get_hex_from_color(self.theme_cls.primary_color)
            )


class ProjectDialogChangeTheme(ProjectBaseDialog):
    def set_list_colors_themes(self):
        for name_theme in palette:
            self.ids.rv.data.append(
                {
                    "viewclass": "ProjectOneLineLeftWidgetItem",
                    "color": get_color_from_hex(colors[name_theme]["500"]),
                    "text": name_theme,
                }
            )
