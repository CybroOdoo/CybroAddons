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


class SubscriptionPlan(models.Model):
    _name = 'subscription.package.plan'
    _description = 'Subscription Package Plan'

    name = fields.Char(string='Plan Name', required=True)
    renewal_value = fields.Char(string='Renewal')
    renewal_period = fields.Selection([('days', 'Day(s)'),
                                       ('weeks', 'Week(s)'),
                                       ('months', 'Month(s)'),
                                       ('years', 'Year(s)')],
                                      default='months')
    renewal_time = fields.Integer(string='Renewal Time Interval',
                                  readonly=True,
                                  compute='_compute_renewal_time',
                                  store=True)
    limit_choice = fields.Selection([('ones', 'Ones'),
                                     ('manual', 'Until Closed Manually'),
                                     ('custom', 'Custom')],
                                    default='ones')
    limit_count = fields.Integer(string='Custom Renewal Limit')
    days_to_end = fields.Integer(string='Days End', readonly=True,
                                 compute='_compute_days_to_end', store=True,
                                 help="Subscription ending date")
    invoice_mode = fields.Selection([('manual', 'Manually'),
                                     ('draft_invoice', 'Draft')],
                                    default='draft_invoice')
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 store=True, domain="[('type', '=', 'sale')]")
    company_id = fields.Many2one('res.company', string='Company', store=True,
                                 default=lambda self: self.env.company)
    short_code = fields.Char(string='Short Code')
    terms_and_conditions = fields.Text(string='Terms and Conditions')
    product_count = fields.Integer(string='Products',
                                   compute='_compute_product_count')
    subscription_count = fields.Integer(string='Subscriptions',
                                        compute='_compute_subscription_count')

    @api.depends('product_count')
    def _compute_product_count(self):
        """ Calculate product count based on subscription plan """
        self.product_count = self.env['product.product'].search_count(
            [('subscription_plan_id', '=', self.id)])

    @api.depends('subscription_count')
    def _compute_subscription_count(self):
        """ Calculate subscription count based on subscription plan """
        self.subscription_count = self.env[
            'subscription.package'].search_count([('plan_id', '=', self.id)])

    @api.depends('renewal_value', 'renewal_period')
    def _compute_renewal_time(self):
        """ This method calculate renewal time based on renewal value """
        for rec in self:
            if rec.renewal_period == 'days':
                rec.renewal_time = int(rec.renewal_value)
            elif rec.renewal_period == 'weeks':
                rec.renewal_time = int(rec.renewal_value) * 7
            elif rec.renewal_period == 'months':
                rec.renewal_time = int(rec.renewal_value) * 28
            elif rec.renewal_period == 'years':
                rec.renewal_time = int(rec.renewal_value) * 364
            if rec.name:
                rec.short_code = str(rec.name[0:3]).upper()

    @api.depends('renewal_time', 'limit_count')
    def _compute_days_to_end(self):
        """ This method calculate days to end for subscription plan based on
        limit count """
        for rec in self:
            if rec.limit_choice == 'ones':
                rec.days_to_end = rec.renewal_time
            if rec.limit_choice == 'manual':
                rec.days_to_end = False
            if rec.limit_choice == 'custom':
                rec.days_to_end = rec.renewal_time * rec.limit_count

    def button_product_count(self):
        """ It displays products based on subscription plan """
        return {
            'name': 'Products',
            'domain': [('subscription_plan_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def button_sub_count(self):
        """ It displays subscriptions based on subscription plan """
        return {
            'name': 'Subscriptions',
            'domain': [('plan_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'subscription.package',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def name_get(self):
        """ It displays record name as combination of short code and
        plan name """
        res = []
        for rec in self:
            res.append((rec.id, '%s - %s' % (rec.short_code, rec.name)))
        return res
