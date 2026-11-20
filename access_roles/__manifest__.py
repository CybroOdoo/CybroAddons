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
    'name': 'Access Roles',
    'version': '20.0.1.0.0',
    'category': 'Security',
    'summary': 'Access Roles for users',
    'description': """Manage user access roles and role-based permissions in Odoo.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail', 'web'],
    'data': [
        'security/access_roles_security.xml',
        'security/ir.access.csv',
        'views/access_role_views.xml',
        'views/role_management_views.xml',
        'views/res_users_views.xml',
        'views/domain_model_views.xml',
        'views/access_role_menus.xml',
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
    'license': 'LGPL-3',
<<<<<<< HEAD
    'installable': True,
=======
    "installable": True,
>>>>>>> 49af41ba33f680f850e6122febbe1b240c576568
    'auto_install': False,
    'application': True,
}
