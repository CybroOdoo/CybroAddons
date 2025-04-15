# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import api, fields, models


class ExtraService(models.Model):
    """
    Model for defining extra services that can be added to a fleet rental
    contract Each service is associated with a product, and the total amount
    is computed based on the quantity and unit price of the product.
    """
    _name = 'extra.service'
    _description = 'Extra Services'

    product_id = fields.Many2one('product.product',
                                 string='Product',
                                 required=True,
                                 help='Description of the extra service.')
    quantity = fields.Float(string='Quantity', default=1.0,
                            required=True,
                            help='Quantity of the extra service.')
    unit_price = fields.Float(string='Unit Price',
                              related='product_id.lst_price', store=True,
                              readonly=False,
                              help='Unit price of the extra service.')
    amount = fields.Float(string='Amount', compute='_compute_amount',
                          store=True,
                          help='Total amount for the extra service.')
    description = fields.Char(string='Description',
                              help='Description of the Product')
    contract_id = fields.Many2one('fleet.rental.contract',
                                  string='Contract Rent',
                                  help='Reference to the vehicle rent.')

    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        """
        Compute the total amount for the extra service based on the
        quantity and unit price. The amount is calculated as
        quantity * unit_price and stored in the 'amount' field.
        """
        for service in self:
            service.amount = service.quantity * service.unit_price




