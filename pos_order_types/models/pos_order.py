# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjana P V  (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################
from odoo import api, fields, models


class PosOrder(models.Model):
    """Extends the POS Order model to include custom delivery type."""
    _inherit = 'pos.order'

    delivery_type = fields.Many2one('delivery.type',
                                    string='Order Type',
                                    help='Selected order type', readonly=True)

    @api.model
    def _order_fields(self, ui_order):
        """Extends the base method to include the delivery type field in
         the order creation process."""
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        if ui_order['delivery_method']:
            order_fields['delivery_type'] = ui_order['delivery_method']['id']
        return order_fields
