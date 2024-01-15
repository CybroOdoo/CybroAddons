# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
{
    'name': 'POS Order Line Mass Edit',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': "Users have the ability to edit POS order lines",
    'description': """A functionality has been implemented where, upon clicking 
    a button, users have the ability to edit POS order lines. This includes the 
    capability to modify the quantity and price of items, and also add 
    discounts through a popup interface""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['point_of_sale'],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_order_line_mass_edit/static/src/xml/pos_mass_edit_button.xml',
            'pos_order_line_mass_edit/static/src/xml/pos_mass_edit_popup.xml',
            'pos_order_line_mass_edit/static/src/js/pos_mass_edit_button.js',
            'pos_order_line_mass_edit/static/src/js/pos_mass_edit_popup.js',
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
