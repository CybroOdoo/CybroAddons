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
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': """Quick POS keyboard shortcuts for faster transactions.""",
    'description': """Easily operate the Point of Sale (POS) system using keyboard shortcuts.
    This module helps users speed up billing and navigation within the POS interface.""",
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
            'odoo_pos_keyboard_shortcut/static/src/js/pos_shortcut_popup.js',
            'odoo_pos_keyboard_shortcut/static/src/xml/pos_shortcut_popup.xml',
            'odoo_pos_keyboard_shortcut/static/src/xml/pos_shortcut_button.xml',
            'odoo_pos_keyboard_shortcut/static/src/js/pos_shortcut_button.js',
            'odoo_pos_keyboard_shortcut/static/src/js/pos_store_patch.js',
            'odoo_pos_keyboard_shortcut/static/src/js/pos_product_screen_patch.js',
            'odoo_pos_keyboard_shortcut/static/src/js/pos_payment_screen_patch.js',
            'odoo_pos_keyboard_shortcut/static/src/js/pos_receipt_screen_patch.js',
            'odoo_pos_keyboard_shortcut/static/src/js/pos_error_popup.js',
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