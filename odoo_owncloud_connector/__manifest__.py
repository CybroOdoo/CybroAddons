# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': "Odoo ownCloud Connector",
    'version': '16.0.1.0.0',
    'category': 'Document Management',
    'summary': 'ownCloud integration for document management',
    'description': 'We Can integrate ownCloud with odoo for managing the '
                   'documents. We can upload and download our documents using'
                   ' this module. Also we can delete the files from the'
                   ' ownCloud.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/owncloud_dashboard_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/owncloud_upload_views.xml'
    ],
    'assets': {
        'web.assets_backend': [
            '/odoo_owncloud_connector/static/src/js/owncloud.js',
            '/odoo_owncloud_connector/static/src/xml/owncloud_dashboard_templates.xml',
            '/odoo_owncloud_connector/static/src/scss/owncloud.scss'
        ]},
    'external_dependencies': {'python': ['pyocclient']},
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
