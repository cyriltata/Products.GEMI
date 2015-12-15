# -*- coding: utf-8 -*-
"""A Folder view that lists Todo Items."""

# Zope imports
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class Todo(BrowserView):
    """A BrowserView to display the Todo listing on a Folder."""

    template = ViewPageTemplateFile("templates/folders_todo.pt")

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return self.template();

