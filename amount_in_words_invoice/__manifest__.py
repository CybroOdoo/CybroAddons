# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
###################################################################################

{
    'name': "Amount in Words in Invoice, Sale Order and Purchase Order",
    'version': '15.0.1.0.0',
    'summary': """Amount in Words in Invoice, Sale Order and Purchase Order""",
    'description': """Amount in Words in Invoice, Sale Order and Purchase Order""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'category': 'Sales',
    'depends': ['sale_management', 'account', 'purchase'],
    'data': [
        'views/account_move.xml',
        'views/sale_order_view.xml',
        'views/sale_order_send_mail.xml',
        'views/sale_order_send_without_confirm_mail.xml',
        'views/purchase_order_view.xml',
        'views/purchase_order_po_send_mail.xml',
        'views/payment_send_mail.xml',
        'views/invoice_send_mail.xml',
        'views/credit_note_mail_send.xml',
        'report/report.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
