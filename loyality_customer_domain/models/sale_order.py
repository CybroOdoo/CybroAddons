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
#############################################################################
from odoo import models


class SaleOrder(models.Model):
    """Apply the customer domain of the loyalty rules to the sale orders."""
    _inherit = 'sale.order'

    def _program_check_compute_points(self, programs):
        """Skip the rules whose customer domain excludes the customer of the
        order, and explain why a program only made of such rules does not
        apply."""
        self.ensure_one()
        customer_context = {'loyalty_customer_id': self.partner_id.id}
        result = super(
            SaleOrder, self.with_context(**customer_context),
        )._program_check_compute_points(programs.with_context(**customer_context))
        result = {program.with_env(self.env): status
                  for program, status in result.items()}
        for program, status in result.items():
            if 'error' in status and program.rule_ids and not any(
                    rule._is_customer_eligible(self.partner_id)
                    for rule in program.rule_ids):
                status['error'] = self.env._(
                    "This program is not available for this customer.")
        return result
