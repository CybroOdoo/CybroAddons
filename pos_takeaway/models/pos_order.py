# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class PosOrder(models.Model):
    """Inheriting pos_order"""
    _inherit = "pos.order"

    is_takeaway = fields.Boolean(string="Is a Takeaway Order",
                                 help="Is a Takeaway Order", default=False, )
    token_number = fields.Char(string="Token Number",
                               help="Token number starts from 1")

    def generate_token(self, uid):
        """
        This function check whether the order is a take-away order or a dine-in.
        If it is a take-away order, it will create the token number for that
        order and returns it.
        :param : uid: the pos order id
        :return : order.token_number: token number of the pos order having the
        order reference uid
        """
        order = self.env['pos.order'].browse(uid)
        order.is_takeaway = True
        if not order.token_number and \
                self.env['res.config.settings'].get_values()[
                    'generate_token']:
            if self.env['res.config.settings'].get_values()[
                       'pos_token']:
                order.token_number = int(
                    self.env['res.config.settings'].get_values()[
                        'pos_token']) + 1
            else:
                order.token_number = 1
            self.env['ir.config_parameter'].sudo().set_param(
                'pos_takeaway.pos_token',
                order.token_number)
            return order.token_number
        else:
            return 0
