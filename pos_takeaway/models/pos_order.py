# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models


class PosOrder(models.Model):
    """
    Adding the fields in model pos order for determining whether the order is a
    take-away or dine-in.
    """
    _inherit = "pos.order"

    is_takeaway = fields.Boolean(string="Is a Takeaway Order",
                                 help="If enabled the order is take away")
    token_number = fields.Char(string="Token Number",
                               help="If enabled token number will start from 1")

    def generate_token(self, uid):
        """
        This function checks whether the order is a take-away order or a
        dine-in.If it is a take-away order, it will create the token number and
        returns it.
        :param : uid: the pos order id
        :return : order.token_number: token number of the pos order having the
        order reference uid
        """
        order = self.env['pos.order'].search([('pos_reference', 'ilike',
                                               "Order " + uid[0])])
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

    def ticket_scheduler(self):
        """ This function will reset the Token to 0 by a cron job. """
        generate_token = self.env['ir.config_parameter'].sudo().get_param(
            'generate_token')
        if generate_token:
            self.env['ir.config_parameter'].sudo().set_param('pos_token', 0)
