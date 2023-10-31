# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
{
    'name': 'Logout Idle User',
    'version': '14.0.1.0.0',
    'summary': 'Auto logout idle user with fixed time',
    'description': """User can fix the timer in the user's profile, if the user
     is in idle mode the user will logout from session 
     automatically""",
    'category': 'Extra Tools',
    'author': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'AGPL-3',
    'depends': ['base'],
    'images': ['static/description/banner.png'],
    'data': [
        'views/res_users_views.xml',
        'views/assets.xml'
    ],
    'qweb': ['static/src/xml/systray.xml'],
    'installable': True,
    'application': False,
    'auto_install': False
}
