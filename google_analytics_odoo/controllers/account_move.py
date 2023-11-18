# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class InvoiceDetails(http.Controller):
    """ This class  contains
           functions for getting invoice details.
           Methods:
               get_invoice_details():
                   Returns the invoice details when confirming the invoice"""

    @http.route('/invoice_analytics', type="json", auth="public")
    def invoice_details(self, **kw):
        """ Returns the invoice details"""
        order = request.env['account.move'].browse(
            int(kw.get('order_id'))).read()
        return {
            'invoice_data': {'name': order[0].get('name'),
                             'amount': order[0].get('amount_total'),
                             'customer': order[0].get('partner_id')[1]},
        }
