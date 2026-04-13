# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from datetime import datetime, time, timedelta

import pytz

from odoo import api, models, fields
from odoo.fields import Datetime


class ResPartner(models.Model):
    """To show the redemption history in the customer's form"""
    _inherit = 'res.partner'

    pos_order_ids = fields.One2many('pos.order', inverse_name="partner_id",
                                    domain="[('partner_id','=',self.id)]")

    def action_view_redemption_history(self):
        """Smart button to view the rewards claimed by the customers"""
        order_id = self.env['pos.order'].search(
            [('partner_id', '=', self.id)]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Redemption History',
            'view_mode': 'tree,form',
            'res_model': 'pos.order.line',
            'domain': [('is_reward_line', '=', 'true'),
                       ('order_id', 'in', order_id)],
            'context': "{'create': False}"
        }

    @api.model
    def get_redemption_frequency_count(self, partner_id, frequency_unit):
        """Count claimed reward lines for the partner in the active period."""
        if not partner_id or frequency_unit not in ('day', 'week', 'month', 'year'):
            return 0

        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        today = fields.Date.context_today(self)

        if frequency_unit == 'day':
            start_date = today
            end_date = today
        elif frequency_unit == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif frequency_unit == 'month':
            start_date = today.replace(day=1)
            if start_date.month == 12:
                next_month = start_date.replace(year=start_date.year + 1, month=1)
            else:
                next_month = start_date.replace(month=start_date.month + 1)
            end_date = next_month - timedelta(days=1)
        else:
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)

        start_local = user_tz.localize(datetime.combine(start_date, time.min))
        end_local = user_tz.localize(datetime.combine(end_date, time.max))
        start_utc = Datetime.to_string(start_local.astimezone(pytz.UTC).replace(tzinfo=None))
        end_utc = Datetime.to_string(end_local.astimezone(pytz.UTC).replace(tzinfo=None))

        domain = [
            ('is_reward_line', '=', True),
            ('order_id.partner_id', '=', partner_id),
            ('create_date', '>=', start_utc),
            ('create_date', '<=', end_utc),
        ]
        return self.env['pos.order.line'].search_count(domain)
