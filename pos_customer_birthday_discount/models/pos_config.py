# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Rahul CK(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models


class PosConfig(models.Model):
    """Set the Birthday discount fields in pos_config model"""
    _inherit = 'pos.config'

    birthday_discount = fields.Boolean(string="Birthday Discount",
                                       help="Enable this field to activate "
                                            "birthday discount")
    discount = fields.Float(string="Discount", help="Percentage of birthday "
                                                    "discount")
    first_order = fields.Boolean(string="Only Apply the discount on the "
                                        "first order on Birthday",
                                 help="Restrict discount to apply only on "
                                      "first order on birthday")

    @api.model
    def check_birthday(self, args):
        """Check the birthday of selected partner"""
        data = {}
        for rec in self.search([]):
            partner_id = self.env['res.partner'].browse(args)
            today = fields.Date.today()
            if rec.birthday_discount and partner_id.birthdate:
                if (partner_id.birthdate.day == today.day and
                        partner_id.birthdate.month == today.month):
                    data = {'birthday': 'True'}
                break
        return data

    @api.model
    def check_pos_order(self, args):
        """Check if any other pos order is created by partner on birthday"""
        data = {'order': 'False'}
        today = fields.Date.today()
        partner_id = self.env['res.partner'].browse(args[0])
        if partner_id.birthdate:
            if (partner_id.birthdate.day == today.day and
                    partner_id.birthdate.month == today.month):
                data['birthday'] = 'True'
                if args[1]:
                    orders = self.env['pos.order'].search(
                        [('partner_id', '=', args[0])]).filtered(
                        lambda r: r.date_order.date() == today)
                    data['order'] = 'True' if len(orders) > 0 else 'False'
        return data
