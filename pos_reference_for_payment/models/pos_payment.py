# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind (odoo@cybrosys.com)
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
            order = self.env['pos.order'].search(
                [('pos_reference', '=', order_list[0]['name'])])
            for rec in order.payment_ids:
                rec.write({
                    'user_payment_reference': order_list[0]['code']
                })
