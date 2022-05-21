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


class SubscriptionInvoice(models.Model):
    _inherit = "account.move"

    is_subscription = fields.Boolean(string='Is Subscription', default=False)
    subscription_id = fields.Many2one('subscription.package',
                                      string='Subscription')

    @api.model_create_multi
    def create(self, vals_list):
        """ It displays subscription in account move """
        for rec in vals_list:
            so_id = self.env['sale.order'].search(
                [('name', '=', rec.get('invoice_origin'))])
            if so_id.is_subscription is True:
                new_vals_list = [{'is_subscription': True,
                                  'subscription_id': so_id.subscription_id}]
                vals_list[0].update(new_vals_list[0])
        return super(SubscriptionInvoice, self).create(vals_list)


class SubscriptionProduct(models.Model):
    _inherit = "product.template"

    is_subscription = fields.Boolean(string='Is Subscription', default=False)
    subscription_plan_id = fields.Many2one('subscription.package.plan',
                                           string='Subscription Plan')
