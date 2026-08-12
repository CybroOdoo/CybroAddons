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
from odoo import fields, models

class AccountMoveLine(models.Model):
    """Extend account move line to support POS product type and control reconciliation behavior."""
    _inherit = "account.move.line"

    product_type = fields.Selection(selection_add=[('pos', 'POS')],
                                    ondelete={'pos': 'cascade'},
                                    help="Type of the product related to this move line.")

    def reconcile(self):
        """Skip reconciliation ONLY if the context flag is explicitly set.
        This prevents POS from auto-paying invoices with POS payments,
        but allows manual 'Pay' button and reconciliation to work.
        """
        if self.env.context.get('skip_pos_invoice_reconciliation'):
            return True
        return super().reconcile()
