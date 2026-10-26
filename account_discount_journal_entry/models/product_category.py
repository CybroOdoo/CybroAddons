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
from odoo import fields, models
from odoo.addons.account.models.product import ACCOUNT_DOMAIN


class ProductCategory(models.Model):
    """Extending this model to add new fields for setting up
    vendor and customer discount accounts.
    """
    _inherit = "product.category"

    # This account will be used for vendor discounts
    vendor_account_discount_id = fields.Many2one(
        'account.account',
        string="Vendor Discount Account",
        company_dependent=True,
        domain=ACCOUNT_DOMAIN,
        help="Account for setting up vendor discounts",
    )
    # This account will be used for customer discounts
    customer_account_discount_id = fields.Many2one(
        'account.account',
        string="Customer Discount Account",
        company_dependent=True,
        domain=ACCOUNT_DOMAIN,
        help="Account for setting up customer discounts",
    )
