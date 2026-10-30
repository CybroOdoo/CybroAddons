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
#############################################################################
from odoo import api, fields, models


class AccountMove(models.Model):
    """
    Extend the AccountMove model to include customer blacklist warnings.

    This class inherits from account.move and displays a warning notification
    when a blacklisted customer is selected on an invoice.
    """
    _inherit = 'account.move'

    partner_blacklist_warning = fields.Text(
        string="Blacklist Warning",
        compute='_compute_partner_blacklist_warning',
        help="Warning message displayed when the customer is blacklisted.",
    )

    @api.depends('partner_id.blacklisted_partner')
    def _compute_partner_blacklist_warning(self):
        """Add warning message on invoice if the customer is blacklisted."""
        for rec in self:
            if rec.partner_id.blacklisted_partner:
                rec.partner_blacklist_warning = self.env._(
                    "The customer %s is marked as blacklisted.",
                    rec.partner_id.name,
                )
            else:
                rec.partner_blacklist_warning = False
