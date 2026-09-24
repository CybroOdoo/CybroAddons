# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LoyaltyCard(models.Model):
    """Inherit loyalty card to add credit limit functionality."""
    _inherit = 'loyalty.card'

    set_limit = fields.Boolean(
        string='Set Limit',
        help="Enable to set a maximum spending limit for this wallet."
    )
    limit = fields.Float(
        string='Spend only',
        help="The maximum amount that can be spent from this wallet."
    )
    used_limit = fields.Float(
        string='Used Limit',
        default=0.0,
        help="Amount of limit that has been consumed."
    )
    balance_limit_amount = fields.Float(
        string='Balance limit Amount',
        compute='_compute_balance_limit',
        store=True,
        help="The remaining spendable amount from the defined limit."
    )

    @api.depends('limit', 'used_limit', 'set_limit')
    def _compute_balance_limit(self):
        """Compute the remaining balance limit based on the set limit and used limit."""
        for rec in self:
            rec.balance_limit_amount = rec.limit - rec.used_limit if rec.set_limit else 0.0

    @api.constrains('limit', 'set_limit')
    def _check_balance_points(self):
        """Ensure that the limit does not exceed the available points."""
        for rec in self:
            if rec.set_limit and rec.balance_limit_amount > rec.points:
                raise ValidationError(_("Your balance is less than your allowed limit. Please reset the limit."))
