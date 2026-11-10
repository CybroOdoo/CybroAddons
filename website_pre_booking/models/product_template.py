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


class ProductTemplate(models.Model):
    """Add pre-booking configuration to products."""
    _inherit = 'product.template'

    pre_book = fields.Boolean(
        string='Pre-booking Available',
        help='Allow customers to reserve this product in advance.',
    )
    from_date = fields.Date(
        string='Available From',
        help='First date on which customers can pre-book this product.',
    )
    to_date = fields.Date(
        string='Available Until',
        help='Last date on which customers can pre-book this product.',
    )
    pre_max_quantity = fields.Integer(
        string='Available Pre-booking Quantity',
        help='Maximum quantity customers can still pre-book.',
    )

    @api.constrains('from_date', 'to_date')
    def _check_pre_booking_dates(self):
        for product in self:
            if (
                product.from_date
                and product.to_date
                and product.from_date > product.to_date
            ):
                raise ValidationError(
                    _('The pre-booking end date must be on or after the'
                      ' start date.')
                )

    @api.constrains('pre_max_quantity')
    def _check_pre_booking_quantity(self):
        for product in self:
            if product.pre_max_quantity < 0:
                raise ValidationError(
                    _('The available pre-booking quantity cannot be negative.')
                )

    def _is_pre_booking_available(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        return bool(
            self.pre_book
            and self.pre_max_quantity > 0
            and (not self.from_date or self.from_date <= today)
            and (not self.to_date or today <= self.to_date)
        )

    def _reserve_pre_booking_quantity(self, quantity):
        self.ensure_one()
        if quantity <= 0:
            return False

        product = self.sudo()
        product.env.cr.execute(
            'SELECT id FROM product_template WHERE id = %s FOR UPDATE',
            [product.id],
        )
        product.invalidate_recordset(['pre_max_quantity'])
        if (
            not product._is_pre_booking_available()
            or product.pre_max_quantity < quantity
        ):
            return False

        product.write({
            'pre_max_quantity': product.pre_max_quantity - quantity,
        })
        return True
