# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################

from odoo import fields, models, api


class SaleOrder(models.Model):
    """ This class is used to inherit sale order"""
    _inherit = 'sale.order'

    subscription_count = fields.Integer(string='Subscriptions',
                                        compute='_compute_subscription_count')

    @api.depends('subscription_count')
    def _compute_subscription_count(self):
        subscription_count = self.env['subscription.package'].search_count(
            [('sale_order', '=', self.id)])
        if subscription_count > 0:
            self.subscription_count = subscription_count
        else:
            self.subscription_count = 0

    def button_subscription(self):
        return {
            'name': 'Subscription',
            'sale_order': False,
            'domain': [('sale_order', '=', self.id)],
            'view_type': 'form',
            'res_model': 'subscription.package',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                "create": False
            }
        }

    def _action_confirm(self):
        if self.subscription_count != 1:
            if self.order_line:
                for line in self.order_line:
                    if line.product_id.is_subscription:
                        this_products_line = []
                        rec_list = [0, 0, {'product_id': line.product_id.id,
                                           'product_qty': line.product_uom_qty,
                                           'unit_price': line.price_unit}]
                        this_products_line.append(rec_list)
                        self.env['subscription.package'].create(
                            {
                                'sale_order': self.id,
                                'reference_code': self.env['ir.sequence'].next_by_code('sequence.reference.code'),
                                'start_date': fields.Date.today(),
                                'stage_id': self.env.ref('subscription_package.draft_stage').id,
                                'partner_id': self.partner_id.id,
                                'plan_id': line.product_id.subscription_plan_id.id,
                                'product_line_ids': this_products_line
                            })
        return super()._action_confirm()


class SubscriptionInherit(models.Model):
    """ This class is used to inherit subscription packages"""
    _inherit = 'subscription.package'

    sale_order_count = fields.Integer()
