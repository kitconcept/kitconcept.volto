# -*- coding: utf-8 -*-
from kitconcept.volto import _
from plone.autoform.interfaces import IFormFieldProvider
from plone.namedfile import field as namedfile
from plone.supermodel import model
from zope.interface import provider
from zope.schema import TextLine


@provider(IFormFieldProvider)
class IPreview(model.Schema):

    preview_image = namedfile.NamedBlobImage(
        title=_(u"label_previewimage", default=u"Preview image"),
        description=u"",
        required=False,
    )

    preview_image_original = namedfile.NamedBlobImage(
        title=_(u"label_preview_image_original", default=u"Preview image (original scale)"),
        description=u"Preview image in the original scale without image cropping.",
        required=False,
    )

    preview_caption = TextLine(
        title=_(u"Preview image caption"),
        description=u"",
        required=False,
    )
