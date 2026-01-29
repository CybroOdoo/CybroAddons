# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
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
import datetime
import pytz
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
            user_tz = self.env.user.tz or self.env.context.get('tz')
            user_pytz = pytz.timezone(user_tz) if user_tz else pytz.utc
            today = datetime.datetime.now().astimezone(user_pytz).replace(
                tzinfo=None)
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
        partner_id = self.env['res.partner'].browse(args[0])
        user_tz = self.env.user.tz or self.env.context.get('tz')
        user_pytz = pytz.timezone(user_tz) if user_tz else pytz.utc
        today = datetime.datetime.now().astimezone(user_pytz).replace(
            tzinfo=None)
        if partner_id.birthdate:
            if (partner_id.birthdate.day == today.day and
                    partner_id.birthdate.month == today.month):
                data['birthday'] = 'True'
                if args[1]:
                    orders = self.env['pos.order'].search([
                        ('partner_id', '=', args[0]),
                        ('date_order', '>=',
                         today.replace(hour=0, minute=0, second=0)),
                        ('date_order', '<=',
                         today.replace(hour=23, minute=59, second=59))])
                    data['order'] = 'True' if orders else 'False'
        return data
