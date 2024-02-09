# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swetha Anand (odoo@cybrosys.com)
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
###############################################################################
{
    'name': 'Simplified POS',
    'version': '16.0.1.1.0',
    'category': 'Point of Sale',
    'summary': 'All aspects of POS on a single page.',
    'description': 'A straightforward point-of-sale system that enables '
                   'payment,order confirmation, and product selection all on '
                   'the same page.',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale'],
    'assets': {
        'point_of_sale.assets': [
            'simplified_pos/static/src/js/ProductScreen.js',
            'simplified_pos/static/src/js/ConfirmationPopup.js',
            'simplified_pos/static/src/js/PrintPopup.js',
            'simplified_pos/static/src/js/ProductScreenPaymentLine.js',
            'simplified_pos/static/src/scss/pos.scss',
            'simplified_pos/static/src/xml/ProductScreen.xml',
            'simplified_pos/static/src/xml/OrderWidget.xml',
            'simplified_pos/static/src/xml/ActionpadWidget.xml',
            'simplified_pos/static/src/xml/ConfirmationPopup.xml',
            'simplified_pos/static/src/xml/PrintPopup.xml',
            'simplified_pos/static/src/xml/PaymentScreenPaymentLine.xml',
            'simplified_pos/static/src/xml/ProductWidgetControlPanel.xml',
            'simplified_pos/static/src/xml/chrome.xml',
        ]
    },
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
