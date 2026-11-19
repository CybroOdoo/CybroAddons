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
    'name': "Dropbox Integration",
    'version': "20.0.1.0.0",
    'category': "Document Management",
    'summary': "Integrate Dropbox with Odoo 20 to upload, preview, and manage files.",
    'description': 'A longer description of what this module does.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup'],
    'data': [
        'security/ir.access.csv',
        'views/res_config_settings_views.xml',
        'views/dropbox_dashboard_views.xml',
        'wizard/authentication_wizard_views.xml',
        'wizard/dropbox_upload_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dropbox_integration/static/src/js/dropbox.js',
            'dropbox_integration/static/src/xml/dropbox_dashboard.xml',
            'dropbox_integration/static/src/scss/dropbox.scss',
        ]
    },
    'external_dependencies': {'python': ['dropbox']},
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'uninstall_hook': 'uninstall_hook',
}
