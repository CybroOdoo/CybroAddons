# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com/>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com/>)
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


class ProductTemplate(models.Model):
    """Inherited product.template class to add fields and functions"""
    _inherit = 'product.template'

    is_auto_generate = fields.Boolean(
        string="Is Auto Generate",
        compute='_compute_is_auto_generate',
        help="Used to hide and show the prefix and digit field based on the "
             "option that we choose in settings"
    )
    prefix = fields.Char(
        string='Prefix',
        help="Prefix value used for generating the sequence"
    )
    digits = fields.Integer(
        string='Digits',
        help="Used to set number of digits contained in a sequence"
    )
    number_next = fields.Integer(
        string='Next Number',
        default=0,
        help="Next sequence number that will be used for auto generation"
    )

    @api.onchange('prefix', 'digits')
    def _onchange_digits_prefix(self):
        """Initialize number_next when configuring prefix or digits"""
        if not self.number_next:
            self.number_next = 0

    def _number_next_actual(self):
        """This function is used to generate the next sequence number"""
        self.ensure_one()
        if self.is_auto_generate and self.tracking in ('lot', 'serial'):
            number_next = (self.number_next or 0) + 1
            self.number_next = number_next
            prefix = self.prefix or ''
            digits = max(0, self.digits or 0)
            return f"{prefix}{str(number_next).zfill(digits)}"
        return False

    @api.depends_context('company')
    @api.depends('tracking')
    def _compute_is_auto_generate(self):
        """This function is used to set value to the field 'is_auto_generate'
        based on the value that we choose in settings page"""
        product_type = self.env['ir.config_parameter'].sudo().get_str(
            'auto_generate_lot_number.serial_number_type'
        )
        auto_generate = self.env['ir.config_parameter'].sudo().get_bool(
            'auto_generate_lot_number.is_auto_generate'
        )
        is_auto = bool(product_type == 'product' and auto_generate)
        for rec in self:
            rec.is_auto_generate = is_auto

    def write(self, values):
        """Ensure number_next is initialized when configuring prefix or digits"""
        res = super().write(values)
        if ('prefix' in values or 'digits' in values) and 'number_next' not in values:
            for rec in self:
                if not rec.number_next:
                    rec.number_next = 0
        return res
