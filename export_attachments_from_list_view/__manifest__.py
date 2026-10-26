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
    'name': 'Export Attachments From List View',
    'version': '20.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Easily export and download attachments from multiple records',
    'description': 'When using dynamic functionality in a model, '
                   'the module can be used to quickly download documents '
                   'from multiple records. Documents and other attachments '
                   'attached to the selected records can be downloaded quickly.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'base_setup'],
    'data': [
        'security/ir.access.csv',
        'views/export_attachment_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/attachment_download_confirmation_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
