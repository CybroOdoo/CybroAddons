# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "Odoo Support Request",
    "version": "17.0.1.0.0",
    "category": "Productivity ",
    "summary": "Create Odoo Support Request To Cybrosys",
    "description": """ This module facilitates the creation of support requests
    to Cybrosys directly from the system tray. It also allows for support requests
    via WhatsApp by providing the necessary details and attaching supporting 
    documents.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/client_support_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'cybrosys_support_client/static/src/js/systray_icons.js',
            'cybrosys_support_client/static/src/xml/systray_icon.xml',
            'cybrosys_support_client/static/src/css/client_support.css',
            'https://cdn.jsdelivr.net/npm/remixicon/fonts/remixicon.css',
        ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
