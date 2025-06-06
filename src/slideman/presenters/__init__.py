"""
SLIDEMAN Presenters package.

This package contains presenter classes that implement the Model-View-Presenter (MVP) pattern.
Presenters handle business logic and coordinate between views (UI) and services.
"""

from .base_presenter import BasePresenter, IView
from .projects_presenter import ProjectsPresenter, IProjectsView
from .slideview_presenter import SlideViewPresenter, ISlideViewView
from .assembly_presenter import AssemblyPresenter, IAssemblyView
from .delivery_presenter import DeliveryPresenter, IDeliveryView
from .keyword_manager_presenter import KeywordManagerPresenter, IKeywordManagerView

__all__ = [
    "BasePresenter",
    "IView", 
    "ProjectsPresenter",
    "IProjectsView",
    "SlideViewPresenter",
    "ISlideViewView",
    "AssemblyPresenter",
    "IAssemblyView",
    "DeliveryPresenter",
    "IDeliveryView",
    "KeywordManagerPresenter",
    "IKeywordManagerView",
]