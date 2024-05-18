# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
###############################################################################
from odoo import api, fields, models


class RequisitionOrder(models.Model):
    """Model for requisition order"""
    _name = 'requisition.order'
    _description = 'Requisition order'

    requisition_product_id = fields.Many2one(
        'employee.purchase.requisition', string="Requisition Product",
        help='Requisition product.')
    state = fields.Selection(
        string='State', related='requisition_product_id.state',
        help="Requisition State")
    requisition_type = fields.Selection(
        string='Requisition Type',
        selection=[
            ('purchase_order', 'Purchase Order'),
            ('internal_transfer', 'Internal Transfer')],
        help='Type of requisition')
    product_id = fields.Many2one(
        'product.product', required=True, string="Product",
        help='Select Product')
    description = fields.Text(
        string="Description",
        compute='_compute_product_id',
        store=True, readonly=False,
        precompute=True, help='Product Description')
    quantity = fields.Integer(string='Quantity', help='Quantity')
    uom = fields.Char(
        related='product_id.uom_id.name', string='Unit of Measure',
        help='Product Uom')
    partner_ids = fields.Many2many('res.partner',
                                   compute='_compute_requisition_type')
    partner_id = fields.Many2one(
        'res.partner', string='Vendor',
        help='Vendor for the requisition', readonly=False, )

    @api.depends('product_id')
    def _compute_product_id(self):
        """Compute product description '[("id", "in", [13, 66, 65, 51] )]'"""
        for option in self:
            if not option.product_id:
                continue
            product_lang = option.product_id.with_context(
                lang=self.requisition_product_id.employee_id.lang)
            option.description = product_lang.get_product_multiline_description_sale()

    @api.depends('requisition_type', 'product_id')
    def _compute_requisition_type(self):
        """Fetching product vendors"""
        self.partner_ids = [data.partner_id.id for data in
                            self.product_id.seller_ids]
