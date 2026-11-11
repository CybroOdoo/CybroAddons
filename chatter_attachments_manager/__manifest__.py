#############################################################################
#
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
    "name": "Chatter Attachment Manager",
    "version": "20.0.1.0.0",
    "category": "Discuss",
    "summary": "Manage, edit, preview, and download attachments in chatter and discuss views.",
    'description': 'A longer description of what this module does.',
    "author": "Cybrosys Techno Solutions",
    "company": "Cybrosys Techno Solutions",
    "maintainer": "Cybrosys Techno Solutions",
    "website": "https://www.cybrosys.com",
    "depends": ["mail"],
    "data": [
        "security/ir.access.csv",
        "views/ir_attachment_views.xml",
        "report/chatter_attachments_manager_report_templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "chatter_attachments_manager/static/lib/fabric/fabric.min.js",
            "chatter_attachments_manager/static/lib/tui/tui-code-snippet.min.js",
            "chatter_attachments_manager/static/lib/tui/tui-color-picker.min.js",
            "chatter_attachments_manager/static/lib/filesaver/FileSaver.min.js",
            "chatter_attachments_manager/static/lib/tui/tui-image-editor.min.js",
            "chatter_attachments_manager/static/lib/tui/tui-image-editor.min.css",
            "chatter_attachments_manager/static/src/attachment_control_panel/attachment_control_panel.js",
            "chatter_attachments_manager/static/src/attachment_control_panel/attachment_control_panel_templates.xml",
            "chatter_attachments_manager/static/src/attachment_image/attachment_image.js",
            "chatter_attachments_manager/static/src/attachment_image/attachment_image_templates.xml",
            "chatter_attachments_manager/static/src/css/chatter_attachment_manager.css",
        ],
    },
    "external_dependencies": {
        "python": ["qrcode"],
    },
    "images": [
        "static/description/banner.jpg",
    ],
    "license": "LGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False,
}
