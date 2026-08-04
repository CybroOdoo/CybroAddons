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
from odoo import api, models, _
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    """Inherits the model account.payment to add Validation Error for
    Restricted Journals"""
    _inherit = 'account.payment'

    @api.model_create_multi
    def create(self, vals):
        """Super Create Method for Restricted journals"""
        res = super(AccountPayment, self).create(vals)
        for val in vals:
            if int(val['journal_id']) in self.env.user.journal_ids.ids:
                raise ValidationError(
                    _('You are restricted to create payment with this journal')
                )
            else:
                return res

    def write(self, vals):
        """Super Write Method for Restricted journals"""
        if vals.get('journal_id'):
            journal_id = int(vals['journal_id'])
            if journal_id in self.env.user.journal_ids.ids:
                raise ValidationError(
                    _('You are restricted to modify payment with this journal')
                )
        return super().write(vals)
