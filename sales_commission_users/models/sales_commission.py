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
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SalesCommission(models.Model):
    """Creating sales commission model."""
    _name = "sales.commission"
    _description = "Sales Commission"

    name = fields.Char(
        string="Commission Name",
        help="Name of the commission.",
        required=True,
    )
    sales_person_ids = fields.Many2many(
        'res.users',
        string='Sales Person',
        help="Salespersons to whom this commission applies.",
    )
    commission_type = fields.Selection(
        string="Commission Type",
        selection=[
            ('standard', 'Standard'),
            ('partner_based', 'Partner Based'),
            ('product_based', 'Product Based'),
            ('discount_based', 'Discount Based'),
        ],
        help="Type of commission calculation.",
    )
    std_commission_perc = fields.Float(
        string='Standard Commission Percentage',
        help="Percentage of the order total awarded as standard commission.",
    )
    affiliated_commission_perc = fields.Float(
        string='Affiliated Partner Commission Percentage',
        help="Commission percentage applied for affiliated partners.",
    )
    non_affiliated_commission_perc = fields.Float(
        string='Non-Affiliated Partner Commission Percentage',
        help="Commission percentage applied for non-affiliated partners.",
    )
    product_based_ids = fields.One2many(
        "product.based.sales.commission",
        'sale_commission_id',
        string='Sales Commission Exceptions',
        help="Product-specific sales commission rules.",
    )
    discount_based_ids = fields.One2many(
        "discount.based.sales.commission",
        'sale_commission_id',
        string='Commission Rules',
        help="Discount-based commission rules.",
    )

    @api.constrains('std_commission_perc', 'affiliated_commission_perc',
                    'non_affiliated_commission_perc')
    def _check_percentages(self):
        """Validate that commission percentage values are between 0 and 100."""
        for rec in self:
            for field_name in (
                'std_commission_perc',
                'affiliated_commission_perc',
                'non_affiliated_commission_perc',
            ):
                val = rec[field_name]
                if val < 0.0 or val > 100.0:
                    raise ValidationError(
                        _("Commission percentage must be between 0 and 100.")
                    )
