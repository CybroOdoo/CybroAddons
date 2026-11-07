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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
# pylint: disable=missing-module-docstring,unknown-option-value,manifest-required-author,manifest-deprecated-key,manifest-superfluous-key,pointless-statement
{
    'name': 'Hide Product Price and Cost',
    'version': '20.0.1.0.0',
    'category': 'Sales',
    'summary': 'Easily hide or show product price and cost based on user groups',
    'description': (
        'The module allows administrators to hide product sales price '
        'and cost price from specific users based on access groups. '
        'Users without the designated permissions cannot see or modify '
        'price and cost fields across product forms, kanban, and list views.'
    ),
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'product'],
    'data': [
        'security/hide_product_price_cost_groups.xml',
        'security/ir.access.csv',
        'views/product_product_views.xml',
        'views/product_template_views.xml',
    ],
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
