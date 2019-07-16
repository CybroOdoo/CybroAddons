# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: LINTO C T(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Point of Sale Discounts',
    'version': '9.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Discounts in the Point of Sale(Fixed and Percentage) ',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'images': ['static/description/banner.jpg'],
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'point_of_sale', 'account', 'report', 'account_accountant'],
    'data': [
        'views/report_paperformat_new.xml',
        'views/templates.xml',
        'views/report_payment_new.xml',
        'views/pos_reports_new_invoice.xml',
        'views/report_saleslines_new.xml',
        'views/report_receipt_new.xml',
        'views/account_invoice_view_pos.xml',
        'views/pos_reports_account_invoice.xml',
        'views/pos_view.xml',
    ],
    'qweb': [
        'static/src/xml/discount.xml'
        ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}

