# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class SaleOrder(models.Model):
    """Inherited sale_order to add additional fields related to quickbook"""
    _inherit = 'sale.order'

    qbooks_sale = fields.Char(string='Sale Order ID', help='Quickbook sale id')
    qbooks_sync_token = fields.Char(string='Sync Token',
                                    help='Quickbook Synchronization token')


class SaleOrderLine(models.Model):
    """Inherited sale_order_line to add additional fields related to
     quickbook"""
    _inherit = 'sale.order.line'

    qbooks_sale_line = fields.Char(string='Sale Line ID',
                                   help='Quickbook sale order line id')
    qbooks_sale = fields.Char(string='Sale Order ID',
                              help='Quickbook sale order id')
    qbooks_sync_token = fields.Char(string='Sync Token',
                                    help='Quickbook Synchronization token')
