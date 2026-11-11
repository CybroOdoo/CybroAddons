# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductVendorUpdate(models.TransientModel):
    """ Wizard which is used to update multiple product details at a time.
        In the wizard we can add various field value for product vendor,
        that values will be updated on the product vendor details"""

    _name = "product.vendor.update"
    _description = "Product vendor update"

    partner_id = fields.Many2one('res.partner', string='Vendor',
                                 help="For choosing the vendor", required=True)
    lead_time = fields.Integer(string='Delivery Lead Time',
                               help='Used to update delivery lead time')
    quantity = fields.Integer(string='Quantity',
                              help='for updating product quantity')
    currency_id = fields.Many2one('res.currency',
                                  default=lambda
                                      self: self.env.company.currency_id,
                                  string='Currency', help='Add currency')
    price_unit = fields.Monetary(string='Price Unit',
                                 help='Used to update the product vendor price')
    validity_from = fields.Date(string="Validity From",
                                help='Used to update validity from date')
    validity_to = fields.Date(string="Validity To",
                              help='Used to update validity to of product')
    vendor_product_name = fields.Char(string="Vendor Product Name",
                                      help='Used to update vendor product name'
                                           ' in product')
    vendor_product_code = fields.Char(string="Vendor Product Code",
                                      help='Used to update vendor product code')

    def action_update_vendor(self):
        """Updating vendor information on selected products"""
        self.ensure_one()
        products = self.env['product.template'].browse(
            self.env.context.get('active_ids', [])).exists()
        # The user must at least be able to read the selected products.
        products.check_access('read')
        # Purchase users may not have write access on product.template, so the
        # vendor lines are created directly (as superuser) on
        # product.supplierinfo instead of writing on the product.
        supplierinfo = self.env['product.supplierinfo'].sudo()
        for product in products:
            supplierinfo.create({
                'partner_id': self.partner_id.id,
                'price': self.price_unit,
                'currency_id': self.currency_id.id,
                'delay': self.lead_time,
                'product_name': self.vendor_product_name,
                'product_code': self.vendor_product_code,
                'min_qty': self.quantity,
                'date_start': self.validity_from,
                'date_end': self.validity_to,
                'product_tmpl_id': product.id,
            })

    @api.onchange('validity_to', 'validity_from')
    def _onchange_validity_to(self):
        """ To check from date is greater than to date """
        for wizard in self:
            if (wizard.validity_from and wizard.validity_to
                    and wizard.validity_to < wizard.validity_from):
                raise ValidationError(
                    _("From date should be less than To date"))