# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahul C K (odoo@cybrosys.com)
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
from odoo import api, fields, models


class PosConfig(models.Model):
    """Set the Birthday discount fields in pos_config model"""
    _inherit = 'pos.config'

    birthday_discount = fields.Boolean(string="Birthday Discount",
                                       help="Enable this field to activate "
                                            "birthday discount")
    discount = fields.Float(string="Discount", help="Percentage of birthday "
                                                    "discount")
    first_order = fields.Boolean(string="Only Apply the discount on the first "
                                        "order on Birthday",
                                 help="Restrict discount to apply only on "
                                      "first order on birthday")

    @api.model
    def check_pos_order(self, partner, first_order):
        """Check if it is the birthday of partner and if no other pos order
        is created by partner on birthday(only if these fields are enabled in
        settings).
        :param partner: id of the partner
        :param first_order: Field 'apply only on first order' is
        enabled in settings or not.
        :return: True value if current day is partner birthday and if it is
        not the first order of partner.
        """
        data = {'order': 'False'}
        partner_id = self.env['res.partner'].browse(partner)
        if partner_id.birthdate == fields.Date.today():
            data['birthday'] = 'True'
            if first_order:
                for rec in self.env['pos.order'].search([('partner_id', '=',
                                                          partner)]):
                    if fields.date.today() == rec.date_order.date():
                        data['order'] = 'True'
                        break
        return data
