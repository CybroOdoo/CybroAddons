# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (<https://www.cybrosys.com>)
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
################################################################################
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
                              help='Ued to update validity to of product')
    vendor_product_name = fields.Char(string="Vendor Product Name",
                                      help='Used to update vendor product name'
                                           ' in product')
    vendor_product_code = fields.Char(string="Vendor Product Code",
                                      help='Used to update vendor product code')

    def action_update_vendor(self):
        """Updating vendor information on selected products"""
        for product in self.env['product.template'].browse(
                self._context['active_ids']):
            product.update({
                'seller_ids': [(0, 0,
                                {
                                    'partner_id': self.partner_id.id,
                                    'price': self.price_unit,
                                    'currency_id': self.currency_id.id,
                                    'delay': self.lead_time,
                                    'product_name': self.vendor_product_name,
                                    'product_code': self.vendor_product_code,
                                    'min_qty': self.quantity,
                                    'date_start': self.validity_from,
                                    'date_end': self.validity_to,
                                })]
            })

    @api.onchange('validity_to')
    def _onchange_validity_to(self):
        """ To check from date is greater than to date """
        if self.validity_to < self.validity_from:
            raise ValidationError(_("From date should be less than To date"))
