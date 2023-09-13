# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    """Inherited model for checking the journal type in account.move."""
    _inherit = 'account.move'

    check_journal = fields.Boolean(string="Check Journal",
                                   help="Compute field for check the current "
                                        "record's journal type ",
                                   compute="_compute_journal")

    def _compute_journal(self):
        """Compute field for showing validation error for restricted journal's
        records"""
        self.check_journal = True
        for rec in self.line_ids:
            if rec.full_reconcile_id:
                payment = self.env['account.payment.register'].search(
                    [('id', '=', rec.full_reconcile_id.id)])
                if payment.journal_id.id in self.env.user.journal_ids.ids:
                    raise ValidationError(_('Restricted journals found.'))
        if self.journal_id.id in self.env.user.journal_ids.ids:
            raise ValidationError(_('Restricted journals found.'))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Function for hiding restricted journals from account.move."""
        if self.journal_id.id in self.env.user.journal_ids.ids:
            self.journal_id = False
        return super(AccountMove, self)._onchange_partner_id()
