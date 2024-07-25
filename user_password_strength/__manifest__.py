# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Farha V C (<https://www.cybrosys.com>)
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
###########################################################################
{
    'name': "User Password Strength",
    'version': "17.0.1.0.0",
    'summary': """ User password strength - restrict weak password""",
    'description': """ Customized setting to restrict weak password which is 
     completely configurable. Also, allows the preset password strength checkup
      while resetting.""",
    'author': "Cybrosys Techno Solutions",
    'company': "Cybrosys Techno Solutions",
    'maintainer': "Cybrosys Techno Solutions",
    'website': "https://cybrosys.com/",
    'category': 'Tools',
    'depends': ['base', 'website'],
    'data': [
        'views/signup_page_view.xml',
        'views/restrict_password.xml',
    ],
    'images': ['static/description/banner.png'],
    'assets': {
            'web.assets_frontend': ['user_password_strength/static/src/js/signup_user.js', ],
    },
    'license': "AGPL-3",
    'installable': True,
    'auto_install': True,
    'application': False
}
