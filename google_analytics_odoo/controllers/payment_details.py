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


class PaymentDetails(http.Controller):
    """ This class  contains
               functions for getting Payment details.
               Methods:
                   get_payment_details();
               Returns the payment details when a customer pays
               through the website"""

    @http.route('/get_payment_details', type="json", auth="public")
    def get_payment_details(self, payments):
        """ Returns the payment details"""
        return {
            'payment': request.env['payment.provider'].sudo().browse(
                int(payments['payment_option_id'])).name,
            'amount': payments['amount'],
            'partner': request.env['res.partner'].sudo().browse(
                int(payments['partner_id'])).name
        }
