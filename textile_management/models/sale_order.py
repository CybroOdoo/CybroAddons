# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prathyunnan R(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
######################################################################################
from odoo import fields, models
from odoo.http import request


class SaleOrder(models.Model):
    """Inherit sale order model to add a field"""
    _inherit = 'sale.order'

    is_textile_sale_order = fields.Boolean(string="Is Textile Sale Order",
                                           help="To check its created from "
                                                "textile module", copy=False)
    comment = fields.Char(string='Comment', readonly=True,
                          help='The comment provided by the customer.')
    rating = fields.Selection([
        ('0', 'Too Bad'), ('1', 'Poor'), ('2', 'Average Quality'),
        ('3', 'Nice'), ('4', 'Good')], string='Rating', readonly=True,
        help='The rating provided by the customer.')

    def _action_confirm(self):
        res = super()._action_confirm()

        # Mark auto-created Manufacturing Orders as textile MOs
        # so they appear in the Textile Management > Manufacturing Orders menu
        for order in self:
            if order.is_textile_sale_order:
                productions = self.env['mrp.production'].search([
                    ('origin', '=', order.name)
                ])
                productions.write({'is_textile_mrp_order': True})

        feedback = None

        if hasattr(request, "session"):
            feedback = request.session.get('checkout_feedback')

        if feedback:
            for order in self:
                order.rating = feedback.get('rating')
                order.comment = feedback.get('comment')

            request.session.pop('checkout_feedback', None)

        return res