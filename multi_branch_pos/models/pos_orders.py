# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana J(<https://www.cybrosys.com>)
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
#############################################################################
"""pos order"""
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class BranchPosOrder(models.Model):
    """inherit pos order to add branch field"""
    _inherit = "pos.order"
    _description = "Point of Sale Orders"

    branch_id = fields.Many2one('res.branch',
                                related='session_id.branch_id',
                                string='Branch', help='Branches allowed',
                                store=True)

    def _generate_pos_order_invoice(self):
        res = super(BranchPosOrder, self)._generate_pos_order_invoice()
        if self.account_move:
            self.account_move.write({'branch_id': self.branch_id})

        return res
