# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': "Export, Delete, Login Log",
    'version': "16.0.1.0.0",
    'category': 'Extra Tools',
    'summary': """Logs information about Export, Delete, Login""",
    'description': """
    This module helps in logging information related to export of records, 
    deleting of records and login details.
    """,
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://cybrosys.com/",
    'depends': ['base','base_setup'],
    'data': [
        'security/ir_module_category_data.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/export_log_views.xml',
        'views/delete_log_views.xml',
        'views/login_user_log_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'export_delete_login_log/static/src/js/export_data.js'
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': True,
    'application': False
}
