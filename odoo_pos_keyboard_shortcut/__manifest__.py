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
    'name': 'POS Keyboard Shortcut',
    'version': '18.0.1.0.0',
    "category": "point of sale",
    'summary': 'To quickly process transactions, use the following POS'
               ' (Point of Sale) keyboard shortcuts',
    'description': """Easily operate the Point of Sale (POS) system by 
     utilizing POS keyboard shortcuts.""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': ['security/ir.model.access.csv',
             'data/ir_sequence_data.xml',
             'views/res_config_settings_views.xml',
             'views/pos_keyboard_shortcut_views.xml',
             ],
    'assets': {
        'point_of_sale._assets_pos': [
            'odoo_pos_keyboard_shortcut/static/src/js/shortcut_popup.js',
            'odoo_pos_keyboard_shortcut/static/src/xml/shortcut_popup.xml',
            'odoo_pos_keyboard_shortcut/static/src/xml/shortcut_button.xml',
            'odoo_pos_keyboard_shortcut/static/src/js/shortcut_button.js',
            'odoo_pos_keyboard_shortcut/static/src/js/product_screen.js',
            'odoo_pos_keyboard_shortcut/static/src/js/payment_screen.js',
            'odoo_pos_keyboard_shortcut/static/src/js/receipt_screen.js',
        ],
    },
    'images': [
        'static/description/banner.jpg',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
