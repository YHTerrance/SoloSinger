from kivy.properties import ListProperty, StringProperty
from kivy.uix.widget import Widget

from kivymd.uix.list import (
    ILeftBody,
    IRightBodyTouch,
    OneLineAvatarListItem,
    OneLineIconListItem,
    TwoLineAvatarListItem,
)

from kivymd.uix.selectioncontrol import MDCheckbox


class ProjectOneLineLeftAvatarItem(OneLineAvatarListItem):
    divider = None
    source = StringProperty()


class ProjectTwoLineLeftAvatarItem(TwoLineAvatarListItem):
    icon = StringProperty()
    secondary_font_style = "Caption"


class ProjectTwoLineLeftIconItem(TwoLineAvatarListItem):
    icon = StringProperty()


class ProjectOneLineLeftIconItem(OneLineAvatarListItem):
    icon = StringProperty()


class ProjectOneLineIconListItem(OneLineIconListItem):
    icon = StringProperty()


class ProjectOneLineLeftWidgetItem(OneLineAvatarListItem):
    color = ListProperty()


class LeftWidget(ILeftBody, Widget):
    pass


class IconRightSampleWidget(IRightBodyTouch, MDCheckbox):
    pass
