# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Aslam A K( odoo@cybrosys.com )
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': "Dropbox Integration",
    'version': "15.0.1.0.0",
    'category': "Document Management",
    'summary': """Upload and Download Dropbox Files from Odoo""",
    'description': """This module was developed to upload files to Dropbox
    storage as well as access files from Dropbox Storage in Odoo""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/authentication_code_views.xml',
        'wizard/dropbox_upload_views.xml',
        'views/res_config_settings_views.xml',
        'views/dropbox_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            '/dropbox_integration/static/src/js/dropbox.js',
            '/dropbox_integration/static/src/scss/dropbox.scss'
        ],
        'web.assets_qweb': [
            '/dropbox_integration/static/src/xml/dropbox_dashboard_templates.xml'
        ],
    },
    'external_dependencies': {'python': ['dropbox']},
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'uninstall_hook': 'uninstall_hook',
}
