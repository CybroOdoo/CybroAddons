# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Surya Gayathry T A (odoo@cybrosys.com)
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
    'name': 'POS Table Name',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Enhanced Alphanumeric Aliases for POS Floor Tables',
    'description': """
        Customizes the Restaurant POS experience by allowing alphanumeric aliases 
        for floor tables. Replaces strict numbering with flexible, user-defined labels.
    """,
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale', 'pos_restaurant'],
    'data': ['views/restaurant_table_views.xml'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_table_name/static/src/css/table_alias.css',
            'pos_table_name/static/src/js/table_alias_logic.js',
            'pos_table_name/static/src/xml/floor_design.xml',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True
}
