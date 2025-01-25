# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class AccountJournal(models.Model):
    """Inherited 'account.journal' model"""
    _inherit = 'account.journal'

    is_fee = fields.Boolean(string='Is Educational fee?',
                            help="Whether educational fee or not.")

    def action_create_new_fee(self):
        """Function to return receipt form with details"""
        view = self.env.ref('education_fee.receipt_form')
        context = self._context.copy()
        context.update({'journal_id': self.id, 'default_journal_id': self.id})
        context.update({'default_move_type': 'out_invoice'})
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': view.id,
            'context': context,
        }
