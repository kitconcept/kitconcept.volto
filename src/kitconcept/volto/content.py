from plone.app.contenttypes.interfaces import IDocument
from plone.dexterity.content import Container
from zope.interface import implementer


@implementer(IDocument)
class Document(Container):
    """ Folderish document """
