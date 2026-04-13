# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
from odoo import fields, models


class PosPayment(models.Model):
    """Class for inherited model pos payment
        Methods:
            get_payment_reference(self, order_list):
                Method to write payment reference to the corresponding order.
                Works through rpc call."""
    _inherit = 'pos.payment'

    user_payment_reference = fields.Char(string='Payment Reference',
                                         help='Payment reference entered by '
                                              'user.')

    def get_payment_reference(self, order_list):
        """Method to write payment reference to the corresponding order.
           Works through rpc call.
            order_list(list):list of dictionary returned from pos with
                order name and payment reference."""
        if order_list:
            for order_data in order_list:
                order = self.env['pos.order'].search(
                    [('pos_reference', '=', order_data['name'])])
                if order:
                    for payment in order.payment_ids:
                        payment.write({
                            'user_payment_reference': order_data['code']
                        })
