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


class SaleOrder(models.Model):
    """
    This class extends the Sale Order model to include custom fields and methods.
    """
    _inherit = "sale.order"

    @api.depends('partner_id')
    def _compute_note(self):
        """
        Compute the value of the 'note' field for draft records based on the
        partner's country sale terms and conditions.
        """
        res = super()._compute_note()
        for order in self:
            if order.state != 'draft':
                continue
            terms = order.partner_id.country_id.sale_terms_condition
            if terms and not is_html_empty(terms):
                order.note = terms
        return res


