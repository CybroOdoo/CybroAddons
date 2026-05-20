# -*- coding: utf-8 -*-
#############################################################################
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

from odoo import fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_id = fields.Many2one('oil.contract', string='Contract', readonly=True, copy=False,
                               help="Oil contract that generated this vendor bill.")

    def action_post(self):
        """Post the journal entry and transition the linked oil contract to billed state."""
        res = super(AccountMove, self).action_post()
        for move in self:
            if move.contract_id and move.state == 'posted':
                move.contract_id.state = 'billed'
        return res
