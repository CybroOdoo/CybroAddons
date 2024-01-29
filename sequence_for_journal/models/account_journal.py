# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok(odoo@cybrosys.com)
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


class AccountJournal(models.Model):
    """inherit account.journal to add fields and methods"""
    _inherit = 'account.journal'

    sequence_id = fields.Many2one('ir.sequence', string='Sequence',
                                  help='Select the sequence or create one')
    step_size = fields.Integer(related='sequence_id.number_next_actual',
                               string='Step',
                               help="Step size, how a sequence's next number"
                                    " is calculated")
    default_step_size = fields.Integer(default=1, string="Default Step Size",
                                       help='Step size of journal')

    @api.onchange('sequence_id')
    def _onchange_sequence_id(self):
        """writing the prefix value to the short code field"""
        self.code = self.sequence_id.prefix
        self.sequence_id.account_journal_id = self._origin.id

    @api.onchange('code')
    def _onchange_code(self):
        """change the value in prefix field in ir.sequence model when the
        value in code field is changed"""
        self.sequence_id.prefix = self.code
