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
    'name': 'Reports and Attachments Preview in Browser',
    'version': '20.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Preview PDF reports and attachments in a new browser tab instead of downloading them.',
    'description': """
     Preview PDF reports and attachments in a new browser tab instead of
     downloading them. Printing a PDF report opens it in a new tab, chatter
     attachments open in a new tab when downloaded, and files in binary
     attachment fields open in a new tab when clicked. Content is served
     inline so the browser displays it, while keeping the original file name
     for saving.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'mail'],
    'assets': {
        'web.assets_backend': [
            'report_attachment_preview/static/src/js/report_utils.js',
            'report_attachment_preview/static/src/js/attachment_list.js',
            'report_attachment_preview/static/src/js/many2x_binary.js',
            'report_attachment_preview/static/src/xml/many2many_binary_field.xml',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
