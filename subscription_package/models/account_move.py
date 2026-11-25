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


class AccountMove(models.Model):
    """ Inherited account move model to add subscription details """
    _inherit = 'account.move'

    is_subscription = fields.Boolean(string='Is Subscription',
                                     help='Indicates whether the subscription is active')
    subscription_id = fields.Many2one('subscription.package',
                                      string='Subscription',
                                      help='Subscription for the invoice')

    @api.model_create_multi
    def create(self, vals_list):
        """ It displays subscription in account move """
        for rec in vals_list:
            if rec.get('invoice_origin'):
                so_id = self.env['sale.order'].search(
                    [('name', '=', rec.get('invoice_origin'))], limit=1)
                if so_id and so_id.is_subscription:
                    so_id.subscription_id.start_date = so_id.subscription_id.next_invoice_date
                    rec.update({
                        'is_subscription': True,
                        'subscription_id': so_id.subscription_id.id,
                    })
        return super().create(vals_list)
