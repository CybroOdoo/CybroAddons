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
    'name': 'Hide Any Menu User & Group Wise',
    'version': '20.0.2.0.0',
    'category': 'Extra Tools',
    'summary': 'Hide or restrict any menu per user or group, set the app order '
               'per team or user, and star favourite menus.',
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
    - Menu Profiles: set the order of the apps and team shortcuts for a
      group of users.
    - Users can arrange their own apps and reset to the team order.
    - Star any menu as a favourite and open it from the navbar.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web'],
    'data': [
        'security/ir.access.csv',
        'wizard/hide_menu_copy_wizard_views.xml',
        'views/res_users_views.xml',
        'views/ir_ui_menu_views.xml',
        'views/hide_menu_profile_views.xml',
        'views/hide_menu_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hide_menu_user/static/src/**/*',
        ],
        'web.assets_tests': [
            'hide_menu_user/static/tests/tours/**/*',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
