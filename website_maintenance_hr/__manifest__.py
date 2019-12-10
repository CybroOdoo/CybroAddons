# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:SAURABH P V(<https://www.cybrosys.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': 'Website Maintenance Request',
    'summary': """Creates maintenance requests from website and notify the employee by e-mail""",
    'version': '12.0.1.0.0',
    'description': """Creates maintenance requests from website and notify the employee by e-mail""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'category': 'Website',
    'depends': ['website', 'mail', 'hr_maintenance'],
    'license': 'AGPL-3',
    'data': [
        'views/templates.xml',
        'views/views.xml',
        'views/mail_template.xml'
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,

}