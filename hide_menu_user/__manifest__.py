# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
{
    'name': 'Hide Any Menu User & Group Wise',
    'version': '19.0.2.0.1',
    'category': 'Extra Tools',
    'summary': 'Hide or restrict any menu item per user or per group in Odoo.',
    'description': """This module provides functionality to hide or restrict menu
    items on a per-user or per-group basis in Odoo.
    Administrators can control which menus each user is allowed to see, so users
    only have access to the relevant parts of the system, improving both security
    and usability. System administrators are never restricted and always keep the
    full menu.
    Features:
    - Hide any menu or sub-menu for a specific user.
    - Restrict a menu for an entire user group at once.
    - Manage all menu restrictions from one central screen under
      Settings > Users & Companies.
    - Copy one user's hidden menus onto other users in a single click.
    - Cascade a menu's restrictions to all of its sub-menus.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/hide_menu_copy_wizard_views.xml',
        'views/res_users_views.xml',
        'views/ir_ui_menu_views.xml',
        'views/hide_menu_menus.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
