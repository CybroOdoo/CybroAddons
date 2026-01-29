# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu P(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class RequisitionProducts(models.Model):
    _name = 'requisition.order'
    _description = 'Requisition order'

    requisition_product_id = fields.Many2one(
        'employee.purchase.requisition', help='Product for the requisition',
        string='Requisition Product')
    state = fields.Selection(string='State',
                             related='requisition_product_id.state',
                             help='State for the requisition order')
    requisition_type = fields.Selection(
        string='Requisition Type',
        selection=[
            ('purchase_order', 'Purchase Order'),
            ('internal_transfer', 'Internal Transfer'),
        ], help='Type of requisition', default='purchase_order')
    product_id = fields.Many2one('product.product', required=True,
                                 help='Product for the requisition',
                                 string="Product")
    description = fields.Text(
        string="Description",
        compute='_compute_description',
        store=True, readonly=False,
        precompute=True, help='Product Description')
    quantity = fields.Integer(string='Quantity', help='Quantity', default=1)
    uom = fields.Char(related='product_id.uom_id.name',
                      string='Unit of Measure', help='Product Uom')
    partner_id = fields.Many2one('res.partner', string='Vendor',
                                 help='Vendor for the requisition')

    @api.depends('product_id')
    def _compute_description(self):
        """compute product description"""
        for option in self:
            if not option.product_id:
                continue
            product_lang = option.product_id.with_context(
                lang=self.requisition_product_id.employee_id.lang)
            option.description = product_lang.get_product_multiline_description_sale()

    @api.onchange('product_id')
    def _onchange_product(self):
        """fetching product vendors"""
        self.partner_id = False
        vendors_list = [data.name.id for data in self.product_id.seller_ids]
        if not vendors_list:
            return False
        return {'domain': {'partner_id': [('id', 'in', vendors_list)]}}
