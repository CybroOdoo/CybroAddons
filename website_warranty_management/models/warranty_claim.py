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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class WarrantyClaim(models.Model):
    """ Warranty claim class to add fields for warranty claim"""
    _name = 'warranty.claim'
    _rec_name = "sale_order_id"
    _description = 'Warranty Claim'
    _inherit = ['mail.thread']

    customer_id = fields.Many2one('res.partner',
                                  string='Customer Name',
                                  help="Customer selection",
                                  required=True)
    sale_order_id = fields.Many2one('sale.order',
                                    help="To select the sale order",
                                    string='Sale Order')
    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 help="To select the product",
                                 required=True)
    warranty_registration_id = fields.Many2one('warranty.registration',
                                              string='Warranty Registration',
                                              help="Link to the warranty registration record")
    claim_type = fields.Selection([
        ('claim', 'Standard Claim'),
        ('renewal', 'Renewal Request')
    ], string='Claim Type', default='claim', help="Type of request")
    partner_id = fields.Many2one('res.users', string='User',
                                 help="To select the partner",
                                 default=lambda self: self.env.user)
    state = fields.Selection(
        [('draft', 'Draft'), ('approved', 'Approved'),
         ('rejected', 'Rejected')], default='draft', String="Status",
        help="To select the state")
    product_expiry_date = fields.Date(
        string='Product Expiry Date', help="To get the product expiry date",
        related='warranty_registration_id.expiry_date',
        store=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        """ Override create to send notification email to sales person"""
        claims = super(WarrantyClaim, self).create(vals_list)
        template = self.env.ref('website_warranty_management.email_template_warranty_claim_notification', raise_if_not_found=False)
        if template:
            for claim in claims:
                if claim.sale_order_id.user_id:
                    claim.with_context(lang=claim.sale_order_id.user_id.lang).message_post_with_source(
                        template,
                        subtype_xmlid='mail.mt_comment',
                    )
        return claims

    def change_status_approved(self):
        """ Function to change the status of the claim to approved"""
        self.state = 'approved'

    def change_status_rejected(self):
        """ Function to change the status of the claim to rejected"""
        self.state = 'rejected'
