# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
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
from odoo import models


class SaleOrder(models.Model):
    """Inherit sale order model for add a button to print
    subscription id card"""
    _inherit = 'sale.order'

    def action_subscription_id_card(self):
        """For printing subscription id card"""
        products = [order.product_id.name for order in self.order_line]
        data = {
            'name': self.partner_id.name,
            'start_date': self.date_order.date(),
            'partner_id': self.partner_id.id,
            'end_date': self.end_date,
            'products': products,
        }
        action = self.env.ref('print_subscription_id_card'
                              '.action_report_subscription_card').report_action(
            None, data=data)
        action.update({'close_on_report_download': True})
        return action
