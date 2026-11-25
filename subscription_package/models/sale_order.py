# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
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


class SaleOrder(models.Model):
    """ This class is used to inherit sale order"""
    _inherit = 'sale.order'

    subscription_count = fields.Integer(string='Subscriptions',
                                        compute='_compute_subscription_count',
                                        help='Subscriptions count')
    is_subscription = fields.Boolean(string='Is Subscription', default=False,
                                     help='Is subscription')
    subscription_id = fields.Many2one('subscription.package',
                                      string='Subscription',
                                      help='Choose the subscription')
    sub_reference = fields.Char(string="Sub Reference Code", store=True,
                                compute="_compute_reference_code",
                                help='Subscription Reference Code')

    @api.model_create_multi
    def create(self, vals_list):
        """ It displays subscription in sale order """
        for vals in vals_list:
            if vals.get('subscription_id'):
                vals['is_subscription'] = True
        return super().create(vals_list)

    @api.depends('subscription_id.reference_code')
    def _compute_reference_code(self):
        """ It displays subscription reference code """
        for order in self:
            order.sub_reference = order.subscription_id.reference_code or False

    def action_confirm(self):
        """ It Changed the stage, to renew, start date for subscription
        package based on sale order confirm """
        res = super().action_confirm()
        for order in self:
            if order.subscription_id and order.state in ['sale', 'done']:
                stage = self.env['subscription.package.stage'].search(
                    [('category', '=', 'progress')], limit=1).id
                values = {
                    'stage_id': stage,
                    'is_to_renew': False,
                    'start_date': fields.Date.today(),
                }
                order.subscription_id.write(values)
        return res

    def _compute_subscription_count(self):
        """ The compute function for the count of
        subscriptions associated with the sale order. """
        for order in self:
            order.subscription_count = self.env[
                'subscription.package'].sudo().search_count(
                [('sale_order_id', '=', order.id)])

    def button_subscription(self):
        """Open the subscription packages associated with the sale order."""
        return {
            'name': 'Subscription',
            'sale_order_id': False,
            'domain': [('sale_order_id', '=', self.id)],
            'res_model': 'subscription.package',
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
            'context': {
                "create": False
            }
        }

    def _action_confirm(self):
        """ The function used to confirm the sale order and
        create subscriptions for subscription products """
        for order in self:
            if order.subscription_count != 1 and order.order_line:
                for line in order.order_line:
                    if line.product_id.is_subscription:
                        this_products_line = [(0, 0, {
                            'product_id': line.product_id.id,
                            'product_qty': line.product_uom_qty,
                            'unit_price': line.price_unit,
                        })]
                        self.env['subscription.package'].create({
                            'sale_order_id': order.id,
                            'reference_code': self.env[
                                'ir.sequence'].next_by_code(
                                'sequence.reference.code'),
                            'start_date': fields.Date.today(),
                            'stage_id': self.env.ref(
                                'subscription_package.draft_stage').id,
                            'partner_id': order.partner_id.id,
                            'plan_id': line.product_id.subscription_plan_id.id,
                            'product_line_ids': this_products_line,
                        })
        return super()._action_confirm()
