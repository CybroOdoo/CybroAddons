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
    'name': 'Record Display Name Manager',
    'version': '20.0.1.0.0',
    'category': 'Technical',
    'summary': "Choose which field is used as the display name (rec_name) "
               "of any model, directly from the user interface.",
    'description': """
     Record Display Name Manager allows you to configure which field is used
     as the display name (rec_name) of any installed model, without writing
     code. Open the Record Display Name Manager app, pick a model and a field,
     and every breadcrumb, many2one field and name search of that model will
     use the chosen field.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'web'],
    'data': [
        'security/ir.access.csv',
        'views/rec_name_config_views.xml',
        'views/rec_name_manager_menus.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
