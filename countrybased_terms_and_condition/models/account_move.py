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
from odoo import api, models
from odoo.tools import is_html_empty


class AccountMove(models.Model):
    """
    Inherits from account.move to add functionality for automatically adding
    the terms and conditions of a customer's country to the narration field of
    an invoice.
    """
    _inherit = "account.move"

    @api.depends('partner_id')
    def _compute_narration(self):
        """Compute the narration field for the invoice."""
        res = super()._compute_narration()
        for move in self:
            if move.state == 'draft' and move.is_sale_document(include_receipts=True):
                terms_condition = move.partner_id.country_id.sale_terms_condition
                if terms_condition and not is_html_empty(terms_condition):
                    move.narration = terms_condition
        return res



