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
from odoo.exceptions import UserError


class WarrantyClaim(models.Model):
    """Warranty claim raised by a customer for a product of a sale order."""
    _name = 'warranty.claim'
    _description = 'Warranty Claim'
    _rec_name = 'sale_order_id'
    _order = 'id desc'

    customer_id = fields.Many2one(
        'res.partner', required=True,
        help='Customer who raised the claim.')
    sale_order_id = fields.Many2one(
        'sale.order', required=True,
        domain="[('partner_id', 'child_of', customer_id),"
               " ('is_warranty_check', '=', True)]",
        help='Sale order the claimed product was bought on.')
    product_id = fields.Many2one(
        'product.product', required=True,
        domain="[('is_warranty_available', '=', True)]",
        help='Product the claim is raised for.')
    user_id = fields.Many2one(
        'res.users', string='Created By',
        default=lambda self: self.env.user,
        help='User who created the claim.')
    description = fields.Text(help='Details of the issue given by the '
                                   'customer.')
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approved'),
         ('rejected', 'Rejected')], default='draft', string='Status',
        help='Status of the claim.')
    product_expiry_date = fields.Date(
        string='Warranty Expiry Date',
        compute='_compute_product_expiry_date', store=True,
        help='Warranty expiry date of the product on the sale order.')

    @api.depends('sale_order_id.order_line.warranty_expiry_date',
                 'product_id')
    def _compute_product_expiry_date(self):
        """Take the expiry date from the order line of the product."""
        for claim in self:
            lines = claim.sale_order_id.order_line.filtered(
                lambda line, product=claim.product_id:
                line.product_id == product and line.warranty_expiry_date)
            claim.product_expiry_date = max(
                lines.mapped('warranty_expiry_date'), default=False)

    def _check_draft(self):
        """Only draft claims can be approved or rejected."""
        if any(claim.state != 'draft' for claim in self):
            raise UserError(self.env._(
                'Only draft claims can be approved or rejected. Reset the '
                'claim to draft first.'))

    def change_status_approved(self):
        """Approve the claim."""
        self._check_draft()
        self.state = 'approved'

    def change_status_rejected(self):
        """Reject the claim."""
        self._check_draft()
        self.state = 'rejected'

    def action_reset_to_draft(self):
        """Reset an approved or rejected claim to draft."""
        self.state = 'draft'
