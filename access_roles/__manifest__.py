# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Access Roles',
    'version': '17.0.1.0.0',
    'category':'Security',
    'sequence': 1,
    'summary': 'Access Roles for users',
    'description': """Access Roles for users""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'mail', 'web'],
    'data': [
            'security/access_roles_security.xml',
            'security/ir.model.access.csv',
            'views/access_role_views.xml',
            'views/role_management_views.xml',
            'views/res_users_views.xml',
            'views/domain_model_views.xml',
            'views/access_role_menus.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'access_roles/static/src/js/chatter.js',
            'access_roles/static/src/js/debug.js',
            'access_roles/static/src/js/views/list_controller.js',
            'access_roles/static/src/js/views/form_controller.js',
            'access_roles/static/src/js/x2many.js',
            'access_roles/static/src/js/form_cog_menu.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
