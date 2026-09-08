# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class CrmLeadLineWM(models.Model):
    """Waste category line quoted on a CRM opportunity before contract creation."""
    _name = 'crm.lead.line'
    _description = 'CRM Lead Waste Category Line'

    lead_id = fields.Many2one(
        'crm.lead',
        string='Lead / Opportunity',
        required=True,
        ondelete='cascade',
    )
    category_id = fields.Many2one(
        'wm.waste.category',
        string='Waste Category',
        required=True,
    )
    product_ids = fields.Many2many(
        'product.product',
        string='Materials',
        domain="[('is_waste_material', '=', True), ('wm_waste_category_id', '=', category_id)]",
    )
    estimated_weight_kg = fields.Float(
        string='Est. Monthly Weight (kg)',
        default=0.0,
    )
    price_unit = fields.Monetary(
        string='Rate per kg',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        related='lead_id.company_currency',
        string='Currency',
    )
    subtotal = fields.Monetary(
        string='Est. Monthly Subtotal',
        compute='_compute_subtotal',
        currency_field='currency_id',
        store=True,
    )

    @api.depends('estimated_weight_kg', 'price_unit')
    def _compute_subtotal(self):
        """
        Calculate the estimated line subtotal for each CRM lead waste service
        line as quantity × unit price, providing the sales estimate before
        contract creation.
        """
        for line in self:
            line.subtotal = line.estimated_weight_kg * line.price_unit
