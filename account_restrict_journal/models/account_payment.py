# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    """Block the creation and modification of payments in restricted journals."""
    _inherit = 'account.payment'

    @api.model_create_multi
    def create(self, vals_list):
        """Create payments and reject the ones using a restricted journal."""
        vals_list = [vals_list] if isinstance(vals_list, dict) else vals_list
        payments = super().create(vals_list)
        if payments.journal_id & self.env.user.journal_ids:
            raise ValidationError(
                self.env._("You are restricted to create payment with this journal"))
        return payments

    def write(self, vals):
        """Prevent moving payments to a restricted journal."""
        if vals.get('journal_id') in self.env.user.journal_ids.ids:
            raise ValidationError(
                self.env._("You are restricted to modify payment with this journal"))
        return super().write(vals)
