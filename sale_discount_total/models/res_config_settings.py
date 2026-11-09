#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Add the sale discount approval settings."""
    _inherit = 'res.config.settings'

    so_order_approval = fields.Boolean(
        string="Sale Discount Approval",
        default=lambda self: (
            self.env.company.so_double_validation == 'two_step'),
        help="Ask for a manager approval when the discount exceeds the "
             "limit.")
    so_double_validation_limit = fields.Float(
        string="Discount limit requires approval in %",
        related='company_id.so_double_validation_limit', readonly=False,
        help="Discount percentage above which a sale order needs the "
             "approval of a manager.")

    def set_values(self):
        """Save the approval setting on the company."""
        res = super().set_values()
        self.company_id.so_double_validation = (
            'two_step' if self.so_order_approval else 'one_step')
        return res
