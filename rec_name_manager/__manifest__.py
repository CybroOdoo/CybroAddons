# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Harshitha AP(<https://www.cybrosys.com>)
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
    'name': 'Record Display Name Manager',
    'version': '18.0.1.0.0',
    'category': 'Technical',
    'summary': 'Dynamically control the display name (rec_name) of any model from the UI',
    'description': """
        Record Display Name Manager allows you to configure which field is used as the
        display name (rec_name) for any installed model — without writing code.
        Simply go to Settings → Record Display Name Manager, pick a model, pick a field,
        and every many2one, breadcrumb, and name_get call for that model will
        use your chosen field.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/rec_name_config_views.xml',
        'views/rec_name_manager_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'rec_name_manager/static/src/js/rec_name_patch.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}