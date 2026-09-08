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


class WmPricingRule(models.Model):
    """Reusable pricing rule defining rate tiers, minimum charges, and applicable contract types."""
    _name = 'wm.pricing.rule'
    _description = 'Pricing Rule'
    _order = 'sequence asc, id desc'

    name = fields.Char(string='Rule Name', required=True, default='New')
    sequence = fields.Integer(string='Sequence', default=10)
    waste_category_id = fields.Many2one('wm.waste.category', string='Waste Category', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', help='Leave empty for All Customers')
    price_per_kg = fields.Float(string='Price per kg', default=0.0)
    min_weight = fields.Float(string='Min Weight (kg)', default=0.0)
    min_charge = fields.Float(string='Min Charge', default=0.0)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.context_today)
    expiry_date = fields.Date(string='Expiry Date')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
