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
from odoo import fields, models


class WmCategoryBillingRule(models.Model):
    """ Model to store category-based billing rules. """
    _name = 'wm.category.billing.rule'
    _description = 'Category Billing Rule'
    _order = 'category_id, effective_date desc'

    category_id = fields.Many2one(
        'wm.waste.category',
        string='Waste Category',
        required=True,
        ondelete='cascade',
    )
    billing_basis = fields.Selection([
        ('per_kg', 'Per KG'),
        ('flat_per_collection', 'Flat per Collection'),
        ('per_m3', 'Per m³'),
    ], string='Billing Basis', default='per_kg', required=True)
    price = fields.Float(string='Price', digits=(16, 2))
    min_weight = fields.Float(string='Minimum Weight (kg)', digits=(16, 2))
    min_charge = fields.Float(string='Minimum Charge', digits=(16, 2))
    partner_id = fields.Many2one('res.partner', string='Partner (Optional)')
    effective_date = fields.Date(string='Effective Date')
    expiry_date = fields.Date(string='Expiry Date')
