from tethys_sdk.base import TethysAppBase


class Campsite(TethysAppBase):
    """
    Tethys app class for Campsite Finder.
    """

    name = 'Campsite Finder'
    description = ''
    package = 'campsite'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'campsite'
    color = '#f39c12'
    tags = ''
    enable_feedback = True
    feedback_emails = []


