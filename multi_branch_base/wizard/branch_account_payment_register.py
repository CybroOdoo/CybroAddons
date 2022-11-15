# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api


class AccountPaymentRegister(models.TransientModel):
    """inherited account payment register wizard models"""
    _inherit = 'account.payment.register'

    branch_id = fields.Many2one('res.branch', store=True, readonly=False)
    journal_id = fields.Many2one('account.journal', store=True, readonly=False,
                                 compute='_compute_journal_id',
                                 domain="[('company_id', '=', company_id), "
                                        "('type', 'in', ('bank', 'cash'))]")

    @api.depends('company_id', 'source_currency_id')
    def _compute_journal_id(self):
        """methode to compute journal id based on current branch"""
        self.ensure_one()
        lines = self.line_ids._origin
        branch = lines.branch_id
        if branch:
            for wizard in self:
                domain = [
                    ('type', 'in', ('bank', 'cash')),
                    ('branch_id', '=', branch.id),
                ]

                journal = self.env['account.journal'].search(
                    domain, limit=1)
                if not journal:
                    domain = [
                        ('type', 'in', ('bank', 'cash')),
                        ('branch_id', '=', False),
                    ]
                    journal = self.env['account.journal'].search(
                        domain, limit=1)
                wizard.journal_id = journal
        else:
            res = super(AccountPaymentRegister, self)._compute_journal_id()
            return res

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        vals.update({'branch_id': self.line_ids.move_id[0].branch_id.id})
        return vals
