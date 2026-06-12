# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': "POS Invoice In Whatsapp",
    'version': '16.0.1.0.0',
    'category': 'Point of Sale',
    'summary': " With the help of this module you can display the price of the"
               " products according to the pricelists in Product Form."
               " Also it allows you to hide the pricelists price from the"
               " product.",
    'description': " With the help of this module you can display"
                   " the price of the products according to "
                   "the pricelists in Product Form. Also it allows you to "
                   "hide the pricelists price from the product.",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['point_of_sale'],
    'data': [
        'data/pos_order_data.xml',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/mail_template_views.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_invoice_in_whatsapp/static/src/ChatterTopbar.css/Popups/SelectOptionPopup.ChatterTopbar.css',
            'pos_invoice_in_whatsapp/static/src/xml/receiptscreen_templates.xml',
            'pos_invoice_in_whatsapp/static/src/js/send_document.js',
            'pos_invoice_in_whatsapp/static/src/xml/Popups/SelectOptionPopup.xml',
            'pos_invoice_in_whatsapp/static/src/Popups/SelectOption.js',
        ]
    },
    'external_dependencies': {"python": ["pdf2image", "html2text"]},
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
