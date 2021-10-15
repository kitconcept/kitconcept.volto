import json
import logging
import os

import transaction
from kitconcept.contentcreator.creator import content_creator_from_folder
from plone import api
from plone.app.multilingual.browser.setup import SetupMultilingualSite
from plone.app.multilingual.setuphandlers import enable_translatable_behavior
from plone.app.portlets.utils import assignment_mapping_from_key
from plone.dexterity.interfaces import IDexterityFTI
from plone.portlets.constants import CONTEXT_CATEGORY
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import INonInstallable
from Products.CMFPlone.utils import get_installer
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.interfaces import IFactory
from zope.container.interfaces import INameChooser
from zope.interface import implementer

logger = logging.getLogger("kitconcept.volto")


@implementer(INonInstallable)
class HiddenProfiles:
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller"""
        return ["kitconcept.volto:uninstall"]


def post_install(context):
    """Post install script"""
    # portal = api.portal.get()
    # create_default_homepage()


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.


def enable_pam(portal):
    # Ensure that portal is portal
    portal = api.portal.get()
    # Setup the plone.app.multilingual data
    sms = SetupMultilingualSite(portal)
    sms.setupSite(portal)
    enable_translatable_behavior(portal)


def ensure_pam_consistency(portal):
    """Makes sure that all the content in a language branch has language"""

    # Ensure that all the objects below an LFR is of the intended language
    pc = getToolByName(portal, "portal_catalog")
    pl = getToolByName(portal, "portal_languages")

    supported_langs = pl.getSupportedLanguages()

    for lang in supported_langs:
        objects = pc.searchResults(path={"query": f"/Plone/{lang}"})

        for brain in objects:
            obj = brain.getObject()
            if not obj.language or obj.language != lang:
                print(f"Setting missing lang to object: {obj.absolute_url()}")
                obj.language = lang

    pc.clearFindAndRebuild()

    transaction.commit()


def change_content_type_title(portal, old_name, new_name):
    """
    change_content_type_title(portal, 'News Item', 'Meldung')
    """
    portal_types = getToolByName(portal, "portal_types")
    news_item_fti = getattr(portal_types, old_name)
    news_item_fti.title = new_name


def disable_content_type(portal, fti_id):
    portal_types = getToolByName(portal, "portal_types")
    document_fti = getattr(portal_types, fti_id, False)
    if document_fti:
        document_fti.global_allow = False


def enable_content_type(portal, fti_id):
    portal_types = getToolByName(portal, "portal_types")
    document_fti = getattr(portal_types, fti_id, False)
    if document_fti:
        document_fti.global_allow = True


def copy_content_type(portal, name, newid, newname):
    """Create a new content type by copying an existing one"""
    portal_types = getToolByName(portal, "portal_types")
    tmp_obj = portal_types.manage_copyObjects([name])
    tmp_obj = portal_types.manage_pasteObjects(tmp_obj)
    tmp_id = tmp_obj[0]["new_id"]
    new_type_fti = getattr(portal_types, tmp_id)
    new_type_fti.title = newname
    portal_types.manage_renameObjects([tmp_id], [newid])


def add_catalog_indexes(context, wanted=None):
    """Method to add our wanted indexes to the portal_catalog."""
    catalog = api.portal.get_tool("portal_catalog")
    indexes = catalog.indexes()
    indexables = []
    for name, meta_type in wanted:
        if name not in indexes:
            catalog.addIndex(name, meta_type)
            indexables.append(name)
    if len(indexables) > 0:
        catalog.manage_reindexIndex(ids=indexables)


def add_behavior(portal_type, behavior):
    fti = queryUtility(IDexterityFTI, name=portal_type)
    new = [
        currentbehavior
        for currentbehavior in fti.behaviors
        if currentbehavior != behavior
    ]
    new.append(behavior)
    fti.behaviors = tuple(new)


def setupNavigationPortlet(
    context,
    name="",
    root=None,
    includeTop=False,
    currentFolderOnly=False,
    bottomLevel=0,
    topLevel=0,
):
    """
    setupNavigationPortlet(portal['vereinigungen']['fachliche-vereinigungen']['sektion-materie-und-kosmos']['gravitation-und-relativitaetstheorie']) # noqa
    """
    from plone.app.portlets.portlets.navigation import (
        Assignment as NavAssignment,
    )  # noqa

    target_manager = queryUtility(
        IPortletManager, name="plone.leftcolumn", context=context
    )
    target_manager_assignments = getMultiAdapter(
        (context, target_manager), IPortletAssignmentMapping
    )

    navtree = NavAssignment(
        includeTop=includeTop,
        currentFolderOnly=currentFolderOnly,
        bottomLevel=bottomLevel,
        topLevel=topLevel,
    )

    if "navigation" not in target_manager_assignments.keys():
        target_manager_assignments["navigation"] = navtree


def setupPortletAt(portal, portlet_type, manager, path, name="", **kw):
    """
    setupPortletAt(portal, 'portlets.Events', 'plone.rightcolumn', '/vereinigungen/fachliche-vereinigungen/sektion-kondensierte-materie/halbleiterphysik') # noqa
    """
    portlet_factory = getUtility(IFactory, name=portlet_type)
    assignment = portlet_factory(**kw)
    mapping = assignment_mapping_from_key(
        portal, manager, CONTEXT_CATEGORY, path, create=True
    )

    if not name:
        chooser = INameChooser(mapping)
        name = chooser.chooseName(None, assignment)

    mapping[name] = assignment


default_lrf_home = {
    "blocks": {
        "15068807-cfc9-444a-97db-8c736809ff52": {"@type": "title"},
        "59d41d8a-ef05-4e21-8820-2a64f5878092": {
            "@type": "text",
            "text": {
                "blocks": [
                    {
                        "key": "618bl",
                        "text": "Nulla porttitor accumsan tincidunt. Sed porttitor lectus nibh. Praesent sapien massa, convallis a pellentesque nec, egestas non nisi. Nulla porttitor accumsan tincidunt. Nulla porttitor accumsan tincidunt. Nulla porttitor accumsan tincidunt. Quisque velit nisi, pretium ut lacinia in, elementum id enim. Vestibulum ac diam sit amet quam vehicula elementum sed sit amet dui. Sed porttitor lectus nibh. Pellentesque in ipsum id orci porta dapibus.",
                        "type": "unstyled",
                        "depth": 0,
                        "inlineStyleRanges": [],
                        "entityRanges": [],
                        "data": {},
                    }
                ],
                "entityMap": {},
            },
        },
    },
    "blocks_layout": {
        "items": [
            "15068807-cfc9-444a-97db-8c736809ff52",
            "59d41d8a-ef05-4e21-8820-2a64f5878092",
        ]
    },
}


def create_default_homepage(context, default_home=default_lrf_home):
    """This method allows to pass a dict with the homepage blocks and blocks_layout keys"""
    portal = api.portal.get()
    # Test for PAM installed
    try:
        is_pam_installed = get_installer(portal, context.REQUEST).isProductInstalled(
            "plone.app.multilingual"
        )
    except:  # noqa
        is_pam_installed = get_installer(portal, context.REQUEST).is_product_installed(
            "plone.app.multilingual"
        )

    if is_pam_installed:
        # Make sure that the LRFs have the blocks enabled
        add_behavior("LRF", "volto.blocks")

        for lang in api.portal.get_registry_record("plone.available_languages"):
            # Do not write them if there are blocks set already
            # Get the attr first, in case it's not there yet (error in docker image)
            if getattr(portal[lang], "blocks", {}) == {} and (
                getattr(portal[lang], "blocks_layout", {}).get("items") is None
                or getattr(portal[lang], "blocks_layout", {}).get("items") == []
            ):
                logger.info(f"Creating default homepage for {lang} - PAM enabled")
                portal[lang].blocks = default_home["blocks"]
                portal[lang].blocks_layout = default_home["blocks_layout"]

    else:
        create_root_homepage(context)


def create_root_homepage(context, default_home=None):
    """It takes a default object:
    {
        "title": "The title",
        "description": "The description",
        "blocks": {...},
        "blocks_layout": [...]
    }
    and sets it as default page in the Plone root object.
    """

    portal = api.portal.get()

    if default_home:
        blocks = default_home["blocks"]
        blocks_layout = default_home["blocks_layout"]
        portal.setTitle(default_home["title"])
        # portal.setDescription(default_home["description"])

        logger.info(
            "Creating custom default homepage in Plone site root - not PAM enabled"
        )
    else:
        blocks = {
            "07c273fc-8bfc-4e7d-a327-d513e5a945bb": {"@type": "title"},
            "4ec81e29-5718-41f7-9d46-309f1144d096": {
                "@type": "slate",
                "plaintext": " Plone 6 is the first CMS on the market that combines the power features, best-in-class security, and scalability of an enterprise CMS with a state-of-the-art JavaScript frontend and an easy-to-use user interface that gives editors full control over the composition of pages. ",
                "value": [
                    {
                        "children": [
                            {"text": ""},
                            {
                                "children": [
                                    {
                                        "text": "Plone 6 is the first CMS on the market that combines the power features, best-in-class security, and scalability of an enterprise CMS with a state-of-the-art JavaScript frontend and an easy-to-use user interface that gives editors full control over the composition of pages."
                                    }
                                ],
                                "type": "strong",
                            },
                            {"text": ""},
                        ],
                        "type": "p",
                    }
                ],
            },
            "16b64850-1cb1-4843-95fc-8b7fe6e74e09": {
                "@type": "slate",
                "plaintext": "Empowering Editors",
                "value": [{"children": [{"text": "Empowering Editors"}], "type": "h2"}],
            },
            "6d0872d4-5b73-455b-ac4f-1495225b7f52": {
                "@type": "slate",
                "plaintext": "Plone 6 is built from the ground up to empower both seasonal and frequent editors to create modern web layouts that automatically adapt to any device.",
                "value": [
                    {
                        "children": [
                            {
                                "text": "Plone 6 is built from the ground up to empower both seasonal and frequent editors to create modern web layouts that automatically adapt to any device. "
                            }
                        ],
                        "type": "p",
                    }
                ],
            },
            "82dcb6d4-3fe1-4378-bc18-2eb6fd652d41": {
                "@type": "slate",
                "plaintext": "The new blocks engine allows editors to build sophisticated page layouts in no time, without the need for any in-depth knowledge of the underlying web technologies.",
                "value": [
                    {
                        "children": [
                            {
                                "text": "The new blocks engine allows editors to build sophisticated page layouts in no time, without the need for any in-depth knowledge of the underlying web technologies."
                            }
                        ],
                        "type": "p",
                    }
                ],
            },
            "77947dbc-7085-413d-bafd-2f212c23f847": {
                "@type": "slate",
                "plaintext": "No Code Content Types, Forms, and Faceted Search",
                "value": [
                    {
                        "children": [
                            {"text": "No Code Content Types, Forms, and Faceted Search"}
                        ],
                        "type": "h2",
                    }
                ],
            },
            "786df958-6209-46fb-90e9-7ef1349ba74a": {
                "@type": "slate",
                "plaintext": "Plone 6 allows creating new content types through the web without the need to write code. Editors can define templates through the web to control the layout of content types.",
                "value": [
                    {
                        "children": [
                            {
                                "text": "Plone 6 allows creating new content types through the web without the need to write code. Editors can define templates through the web to control the layout of content types."
                            }
                        ],
                        "type": "p",
                    }
                ],
            },
            "4fbebd18-0d13-466a-a65b-43fb885a89e7": {
                "@type": "slate",
                "plaintext": "Creating forms and sophisticated faceted search user interfaces are possible entirely through the web and become a no-brainer with Plone 6.",
                "value": [
                    {
                        "children": [
                            {
                                "text": "Creating forms and sophisticated faceted search user interfaces are possible entirely through the web and become a no-brainer with Plone 6."
                            }
                        ],
                        "type": "p",
                    }
                ],
            },
            "22ff9890-5d07-4786-ad16-10ca39cb7cd5": {
                "@type": "slate",
                "plaintext": "Ready for Prime Time",
                "value": [
                    {"children": [{"text": "Ready for Prime Time"}], "type": "h2"}
                ],
            },
            "10eca87d-78cb-4cb0-a8c5-cd1a495b2206": {
                "@type": "slate",
                "plaintext": "Plone 6 comes with a rich ecosystem of more than 100 add-on products. The new software stack that powers Plone 6 (Volto, REST API, Plone Backend) has been used in production for more than four years. Plone 6 already powers high-profile government websites, university websites, and intranets around the globe today.´",
                "value": [
                    {
                        "children": [
                            {
                                "text": "Plone 6 comes with a rich ecosystem of more than 100 add-on products. The new software stack that powers Plone 6 (Volto, REST API, Plone Backend) has been used in production for more than four years. Plone 6 already powers high-profile government websites, university websites, and intranets around the globe today.´"
                            }
                        ],
                        "type": "p",
                    }
                ],
            },
            "627f0450-9e58-44db-b626-d4de6530d0cb": {
                "@type": "slate",
                "plaintext": "Ready When You Are",
                "value": [{"children": [{"text": "Ready When You Are"}], "type": "h2"}],
            },
            "8e4dbd99-08ef-4dfb-a3e3-b1f1e005ede4": {
                "@type": "slate",
                "plaintext": "Plone 6 will continue to be shipped with a modernized version of the Plone “Classic” user interface. Plone 6 will be a Long Term Support (LTS) release with an extended support period. This will give you all the time you need to adapt your existing Plone site to the new world of Plone 6 if you are not ready yet.",
                "value": [
                    {
                        "children": [
                            {
                                "text": "Plone 6 will continue to be shipped with a modernized version of the Plone “Classic” user interface. Plone 6 will be a Long Term Support (LTS) release with an extended support period. This will give you all the time you need to adapt your existing Plone site to the new world of Plone 6 if you are not ready yet."
                            }
                        ],
                        "type": "p",
                    }
                ],
            },
            "41663271-68b9-4d5e-80b0-3b3def2ca01e": {
                "@type": "slate",
                "plaintext": "",
                "value": [{"children": [{"text": "\n"}], "type": "p"}],
            },
        }
        blocks_layout = {
            "items": [
                "07c273fc-8bfc-4e7d-a327-d513e5a945bb",
                "4ec81e29-5718-41f7-9d46-309f1144d096",
                "16b64850-1cb1-4843-95fc-8b7fe6e74e09",
                "6d0872d4-5b73-455b-ac4f-1495225b7f52",
                "82dcb6d4-3fe1-4378-bc18-2eb6fd652d41",
                "77947dbc-7085-413d-bafd-2f212c23f847",
                "786df958-6209-46fb-90e9-7ef1349ba74a",
                "4fbebd18-0d13-466a-a65b-43fb885a89e7",
                "22ff9890-5d07-4786-ad16-10ca39cb7cd5",
                "10eca87d-78cb-4cb0-a8c5-cd1a495b2206",
                "627f0450-9e58-44db-b626-d4de6530d0cb",
                "8e4dbd99-08ef-4dfb-a3e3-b1f1e005ede4",
                "41663271-68b9-4d5e-80b0-3b3def2ca01e",
            ]
        }

        portal.setTitle("Welcome to Plone 6!")
        portal.setDescription(
            "Plone 6 is the first CMS on the market that combines enterprise features with a modern, user-friendly, state-of-the-art JavaScript frontend."
        )

        logger.info("Creating default homepage in Plone site root - not PAM enabled")

    # Common part
    if not getattr(portal, "blocks", False):
        portal.manage_addProperty("blocks", json.dumps(blocks), "string")

    if not getattr(portal, "blocks_layout", False):
        portal.manage_addProperty(
            "blocks_layout", json.dumps(blocks_layout), "string"
        )  # noqa


def import_example_content(context):
    portal = api.portal.get()

    if "news" in portal.objectIds():
        api.content.delete(obj=portal["news"])

    if "events" in portal.objectIds():
        api.content.delete(obj=portal["events"])

    if "Members" in portal.objectIds():
        api.content.delete(obj=portal["Members"])

    # enable content non-globally addable types just for initial content
    # creation
    TEMP_ENABLE_CONTENT_TYPES = ["Folder"]
    for content_type in TEMP_ENABLE_CONTENT_TYPES:
        enable_content_type(portal, content_type)

    content_creator_from_folder(
        folder_name=os.path.join(os.path.dirname(__file__), "content_creator"),
        base_image_path=os.path.join(os.path.dirname(__file__), "content_images"),
    )

    # disable again content non-globally addable types just for initial content
    # creation
    for content_type in TEMP_ENABLE_CONTENT_TYPES:
        disable_content_type(portal, content_type)
