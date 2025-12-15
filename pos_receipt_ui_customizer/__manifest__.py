# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Neeraj JR (<https://www.cybrosys.com>)
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
    'name': 'POS Receipt UI Customizer',
    'version': '18.0.1.0.0',
    'category': 'Point of Sale',
    'live_test_url': 'https://www.youtube.com/watch?v=sHQUam5F5Qs',
    'summary': "POS Receipt, Receipt Design, POS Receipt Template, Design "
               "Report, Custom Receipt, POS Report, Customise Receipt, Odoo18, "
               "Odoo Apps",
    'description': "Option to select the customised Receipts for each POS. So, "
                   "we can easily updated the Receipt Design for better styles",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/pos_receipt_design1_data.xml',
        'data/pos_receipt_design2_data.xml',
        'data/pos_receipt_design3_data.xml',
        'views/pos_receipt_views.xml',
        'views/pos_config_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_receipt_ui_customizer/static/src/js/receipt_design.js',
            'pos_receipt_ui_customizer/static/src/xml/order_receipt.xml',
        ],
        'web.assets_backend': [
            'pos_receipt_ui_customizer/static/src/js/layout_customisation.js',
            'pos_receipt_ui_customizer/static/src/xml/action.xml',
            'pos_receipt_ui_customizer/static/src/css/style.css',
            'https://cdn.jsdelivr.net/npm/medium-editor@5.23.3/dist/js/medium-editor.min.js',
            'https://cdn.jsdelivr.net/npm/medium-editor@5.23.3/dist/css/medium-editor.min.css',
            'https://cdn.jsdelivr.net/npm/medium-editor@5.23.3/dist/css/themes/default.min.css',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False
}
