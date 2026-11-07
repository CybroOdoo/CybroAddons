# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
{
    "name": "Chatter Attachments as ZIP",
    "version": "20.0.1.0.0",
    "category": "Extra Tools",
    "summary": """Download All Chatter Attachments As A Single Zip File.""",
    "description": "This module helps to download all chatter attachments in a"
                   "single zip file.",
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ['mail'],
    "assets": {
        "web.assets_backend": [
            "chatter_attachments_as_zip/static/src/js/chatter.js",
            "chatter_attachments_as_zip/static/src/xml/chatter.xml",
        ],
        "web.assets_unit_tests": [
            "chatter_attachments_as_zip/static/tests/**/*",
            ("remove", "chatter_attachments_as_zip/static/tests/tours/**/*"),
        ],
        "web.assets_tests": [
            "chatter_attachments_as_zip/static/tests/tours/**/*",
        ],
    },
    "images": ["static/description/banner.jpg"],
    "license": "LGPL-3",
    "installable": True,
    "auto_install": False,
    "application": False,
}
