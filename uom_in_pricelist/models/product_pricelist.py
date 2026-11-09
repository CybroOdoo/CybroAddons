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
from odoo import models
from odoo.fields import Domain


class ProductPricelist(models.Model):
    """ Inherits the Product Pricelist to support product_uom_id filtering """
    _inherit = "product.pricelist"

    def _get_applicable_rules_domain(
        self, products, *, date=None, quantity=None, uom=None, **kwargs
    ):
        """ Include product_uom_id in candidate rules search domain. """
        domain = super()._get_applicable_rules_domain(
            products, date=date, quantity=quantity, uom=uom, **kwargs
        )
        if uom:
            domain &= Domain("product_uom_id", "=", False) | Domain("product_uom_id", "=", uom.id)
        return domain

    def _compute_price_rule(
        self, products, quantity=1.0, *args, currency=None, uom=None, date=False,
        compute_price=True, **kwargs
    ):
        """ Inherited to support legacy positional calls while executing
        Odoo 20 standard price rule resolution. """
        if args:
            if len(args) >= 1 and currency is None:
                currency = args[0]
            if len(args) >= 2 and uom is None:
                uom = args[1]
            if len(args) >= 3 and not date:
                date = args[2]
            if len(args) >= 4:
                compute_price = args[3]

        return super()._compute_price_rule(
            products,
            quantity,
            currency=currency,
            uom=uom,
            date=date,
            compute_price=compute_price,
            **kwargs,
        )
