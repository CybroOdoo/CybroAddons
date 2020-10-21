# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jesni Banu and Nilmar Shereef(odoo@cybrosys.com)
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
#############################################################################

{
    'name': 'Laundry Management',
    'version': '14.0.1.0.0',
    'summary': """Complete Laundry Service Management""",
    'description': 'This module is very useful to manage all process of laundry service',
    "category": "Industries",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['base', 'mail', 'sale', 'account', 'uom'],
    'data': [
        'data/data.xml',
        'security/laundry_security.xml',
        'security/ir.model.access.csv',
        'views/laundry_view.xml',
        'views/washing_view.xml',
        'views/config_view.xml',
        'views/laundry_report.xml',
        'views/laundry_label.xml',
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
