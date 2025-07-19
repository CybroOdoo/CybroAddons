# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
    'name': "POS Discount Manager Approval",
    'version': '18.0.1.0.0',
    'category': 'Point Of Sale',
    'summary': "Discount limit for each employee in every  point of sale""",
    'description': """This module helps you to set a discount limit for each 
    employee in every  point of sale.It facilitate the manager  approval when 
    discount over the limit of employee""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': "Cybrosys Techno Solutions",
    'website': "http://www.cybrosys.com",
    'depends': ['pos_discount', 'hr'],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_discount_manager/static/src/js/payment_screen.js',
            ]
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
