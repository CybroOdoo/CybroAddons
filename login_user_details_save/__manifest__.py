# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaroop N P (odoo@cybrosys.com)
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
    'name': "Save User's Login info",
    'category': 'Extra Tools',
    'version': '16.0.1.0.0',
    'description': """
        This app allows us to save our login info , our name will be 
        displayed in login page and we can click on it and it automatically 
        fills our username
    """,
    'summary': """
        Allows us to save our login info  for easier access next time
    """,
    'author': "Cybrosys Techno Solutions",
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'website', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/logout_popup_view.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'login_user_details_save/static/src/js/logout_replace.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
