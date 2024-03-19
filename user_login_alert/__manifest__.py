# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
{
    'name': 'User Login Alert',
    'version': '17.0.1.0.0',
    'category': 'Extra Tools',
    'summary': """Secure Odoo account by alerts user about any login 
     happened from any systems""",
    'description': """Secure your Odoo account by alerts at right time. If any
     successful login to user's account happens, an alert mail will be send to 
     user with the browser and IP details.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer ': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['mail'],
    'data': [
        'security/user_login_alert_groups.xml',
        'views/res_users_views.xml',
    ],
    'external_dependencies': {'python': ['httpagentparser']},
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
