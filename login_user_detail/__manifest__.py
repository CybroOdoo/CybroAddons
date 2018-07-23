# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2016-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': "User Log Details",
    'version': '11.0.2.0.0',
    'summary': """Login User Details & IP Address""",
    'description': """This module records login information of user""",
    'author': "Cybrosys Techno Solutions ",
    'company': "Cybrosys Techno Solutions ",
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'category': 'Tools',
    'depends': ['base'],
    'license': 'AGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/login_user_views.xml'],
    'demo': [],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
}
