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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """ In this class we are inheriting the model 'sale order' and adding a new
    field for signature. """
    _inherit = 'sale.order'

    sale_person_signature = fields.Binary(
        string='Signature',
        help="Field for adding the signature of the salesperson",
    )
    is_check_signature = fields.Boolean(
        compute='_compute_signature_flags',
        help="Check if user is salesperson and settings field "
             "'is_sale_document_approve' is enabled",
        string="Check Signature",
    )
    is_user_salesperson = fields.Boolean(
        string="User Salesperson",
        compute="_compute_signature_flags",
        help="Check if user is salesperson",
    )
    is_settings_approval = fields.Boolean(
        string="Sale approval enabled",
        compute="_compute_signature_flags",
        help="Check if sale approval enabled",
    )

    @api.depends('user_id', 'sale_person_signature', 'sale_order_template_id')
    @api.depends_context('uid')
    def _compute_signature_flags(self):
        """Compute UI helper booleans used by the form view."""
        approve_enabled = self.env['ir.config_parameter'].sudo().get_bool(
            'sales_person_signature.sale_document_approve',
        )
        current_user = self.env.user
        for rec in self:
            rec.is_settings_approval = approve_enabled
            rec.is_user_salesperson = approve_enabled and rec.user_id == current_user
            rec.is_check_signature = approve_enabled and bool(rec.sale_person_signature)

    def action_confirm(self):
        """Override action_confirm to enforce salesperson signature validation."""
        approve_enabled = self.env['ir.config_parameter'].sudo().get_bool(
            'sales_person_signature.sale_document_approve',
        )
        if approve_enabled:
            for order in self:
                if not order.sale_person_signature:
                    raise ValidationError(
                        self.env._("Salesperson signature is required before confirming the quotation."),
                    )
        return super().action_confirm()
