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


class SubscriptionPackagePlan(models.Model):
    _name = 'subscription.package.plan'
    _description = 'Subscription Package Plan'

    name = fields.Char(string='Plan Name', required=True,
                       help='The name of the subscription plan.')
    renewal_value = fields.Char(string='Renewal',
                                help='A descriptive value indicating the '
                                     'renewal status or details for the '
                                     'subscription plan.')
    renewal_period = fields.Selection([('days', 'Day(s)'),
                                       ('weeks', 'Week(s)'),
                                       ('months', 'Month(s)'),
                                       ('years', 'Year(s)')],
                                      default='months',
                                      help='Select the unit of time for the '
                                           'renewal period of the '
                                           'subscription plan.')
    renewal_time = fields.Integer(string='Renewal Time Interval',
                                  compute='_compute_renewal_time',
                                  store=True,
                                  help='The computed renewal time interval '
                                       'for the subscription plan, based on '
                                       'the selected renewal period.')
    limit_choice = fields.Selection([('ones', 'Once'),
                                     ('manual', 'Until Closed Manually'),
                                     ('custom', 'Custom')],
                                    default='ones',
                                    help='Select the limit choice for the '
                                         'subscription plan, specifying how '
                                         'long it will be active.')
    limit_count = fields.Integer(string='Custom Renewal Limit',
                                 help='Specify the custom renewal limit for '
                                      'the subscription plan. This field is '
                                      'relevant when the "Limit Choice" is '
                                      'set to "Custom".')
    days_to_end = fields.Integer(string='Days End', readonly=True,
                                 compute='_compute_days_to_end', store=True,
                                 help="Subscription ending date")
    invoice_mode = fields.Selection([('manual', 'Manually'),
                                     ('draft_invoice', 'Draft')],
                                    default='draft_invoice',
                                    help='Select the invoice mode for the '
                                         'subscription plan, specifying '
                                         'whether invoices are generated '
                                         'manually or in draft state.')
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 domain="[('type', '=', 'sale')]")
    company_id = fields.Many2one('res.company', string='Company', store=True,
                                 default=lambda self: self.env.company)
    short_code = fields.Char(string='Short Code', compute='_compute_short_code',
                             store=True, readonly=False)
    terms_and_conditions = fields.Text(string='Terms and Conditions')
    product_count = fields.Integer(string='Products',
                                   compute='_compute_product_count')
    subscription_count = fields.Integer(string='Subscriptions',
                                        compute='_compute_subscription_count')

    @api.depends('name')
    def _compute_short_code(self):
        """ Compute short code from name if not manually set """
        for rec in self:
            if rec.name and not rec.short_code:
                rec.short_code = str(rec.name[0:3]).upper()

    def _compute_product_count(self):
        """ Calculate product count based on subscription plan """
        for rec in self:
            rec.product_count = self.env['product.product'].search_count(
                [('subscription_plan_id', '=', rec.id)])

    def _compute_subscription_count(self):
        """ Calculate subscription count based on subscription plan """
        for rec in self:
            rec.subscription_count = self.env[
                'subscription.package'].search_count([('plan_id', '=', rec.id)])

    @api.depends('renewal_value', 'renewal_period')
    def _compute_renewal_time(self):
        """ This method calculate renewal time based on renewal value """
        for rec in self:
            try:
                val = int(rec.renewal_value) if rec.renewal_value else 1
            except (ValueError, TypeError):
                val = 1
            if val <= 0:
                val = 1
            if rec.renewal_period == 'days':
                rec.renewal_time = val
            elif rec.renewal_period == 'weeks':
                rec.renewal_time = val * 7
            elif rec.renewal_period == 'months':
                rec.renewal_time = val * 28
            elif rec.renewal_period == 'years':
                rec.renewal_time = val * 364
            else:
                rec.renewal_time = val

    @api.depends('renewal_time', 'limit_count', 'limit_choice')
    def _compute_days_to_end(self):
        """ This method calculate days to end for subscription plan based on
        limit count """
        for rec in self:
            limit = rec.limit_count if rec.limit_count and rec.limit_count > 0 else 1
            if rec.limit_choice == 'ones':
                rec.days_to_end = rec.renewal_time
            elif rec.limit_choice == 'manual':
                rec.days_to_end = 0
            elif rec.limit_choice == 'custom':
                rec.days_to_end = rec.renewal_time * limit
            else:
                rec.days_to_end = rec.renewal_time

    def button_product_count(self):
        """ It displays products based on subscription plan """
        return {
            'name': 'Products',
            'res_model': 'product.product',
            'domain': [('subscription_plan_id', '=', self.id)],
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
            'context': {
                'default_is_subscription': True,
            },
        }

    def button_sub_count(self):
        """ It displays subscriptions based on subscription plan """
        return {
            'name': 'Subscriptions',
            'domain': [('plan_id', '=', self.id)],
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    @api.depends('short_code', 'name')
    def _compute_display_name(self):
        """ It displays record name as combination of short code and
        plan name """
        for rec in self:
            if rec.short_code and rec.name:
                rec.display_name = f"{rec.short_code} - {rec.name}"
            else:
                rec.display_name = rec.name or ""
