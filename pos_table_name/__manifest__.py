# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
{
    "name": "POS Table Name",
    "version": "18.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Add alphanumeric table name without breaking existing POS logic",
    "description": "Allows assigning alphanumeric, customized names to POS restaurant tables, overriding standard numeric identifiers.",
    "depends": [
        "point_of_sale",
        "pos_restaurant",
    ],
    "data": [
        "views/custom_restaurant_table_views.xml",
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_table_name/static/src/js/custom_restaurant_table.js',
            'pos_table_name/static/src/xml/custom_floor_screen.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    "license": "AGPL-3",
    "installable": True,
    "application": False,

    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'auto_install': False,
}
