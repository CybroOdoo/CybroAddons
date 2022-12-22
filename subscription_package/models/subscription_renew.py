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

from odoo import api, models, fields
import datetime


class SubscriptionSaleOrder(models.Model):
    _inherit = "sale.order"

    is_subscription = fields.Boolean(string='Is Subscription', default=False)
    subscription_id = fields.Many2one('subscription.package',
                                      string='Subscription')
    sub_reference = fields.Char(string="Sub Reference Code", store=True,
                                compute="_compute_reference_code")

    @api.model
    def create(self, vals):
        """ It displays subscription in sale order """
        if vals.get('is_subscription') is True:
            new_vals = [{
                'is_subscription': True,
                'subscription_id': vals.get('subscription_id'),
            }]
            vals.update(new_vals[0])
            return super(SubscriptionSaleOrder, self).create(vals)
        else:
            return super(SubscriptionSaleOrder, self).create(vals)

    @api.depends('subscription_id')
    def _compute_reference_code(self):
        """ It displays subscription reference code """
        self.sub_reference = self.env['subscription.package'].search(
            [('id', '=', int(self.subscription_id.id))]).reference_code

    def action_confirm(self):
        """ It Changed the stage, to renew, start date for subscription
        package based on sale order confirm """

        res = super(SubscriptionSaleOrder, self).action_confirm()
        sale_order = self.subscription_id.sale_order
        so_state = self.search([('id', '=', sale_order.id)]).state
        if so_state in ['sale', 'done']:
            stage = self.env['subscription.package.stage'].search(
                [('category', '=', 'progress')], limit=1).id
            values = {'stage_id': stage, 'to_renew': False,
                      'start_date': datetime.datetime.today()}
            self.subscription_id.write(values)
        return res
