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


class IrSequence(models.Model):
    """inherit ir.sequence to add fields and methods"""
    _inherit = "ir.sequence"

    account_journal_id = fields.Many2one('account.journal',
                                         help="To add the prefix entered in "
                                              "sequence to journal",
                                         string="Journals")

    @api.onchange('prefix')
    def _onchange_prefix(self):
        """change the value in code field in account.journal model when
        value in prefix changed"""
        self.account_journal_id.code = self.prefix
