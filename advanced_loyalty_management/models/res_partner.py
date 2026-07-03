# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models, fields


class ResPartner(models.Model):
    """To show the redemption history in the customer's form"""
    _inherit = 'res.partner'

    pos_order_ids = fields.One2many('pos.order', inverse_name="partner_id",
                                    domain="[('partner_id','=',self.id)]")

    def _load_pos_data_fields(self,config_id):
        """To load more fields in the model res.partner"""
        result = super()._load_pos_data_fields(config_id)
        result += ['pos_order_ids']
        return result

    def action_view_redemption_history(self):
        """Smart button to view the rewards claimed by the customers"""
        order_ids = self.env['pos.order'].search(
            [('partner_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Redemption History',
            'view_mode': 'list,form',
            'res_model': 'pos.order.line',
            'domain': [('is_reward_line', '=', 'true'),
                       ('order_id', 'in', order_ids)],
            'context': "{'create': False}"
        }

    @api.model
    def check_redemption(self, pid):
        """To check number of times the reward is claimed"""
        order = self.env['pos.order'].search([('partner_id', '=', pid[0])])
        data = []
        date = []
        order_line = self.env['pos.order.line'].search(
            [('is_reward_line', '=', 'true'), ('order_id', 'in', order.ids)])
        for line in order_line:
            data.append(line.order_id.id)
            date.append(line.create_date.date())
        return data, date
