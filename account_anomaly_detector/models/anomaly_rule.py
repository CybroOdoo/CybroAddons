# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields, api, _


class AccountAnomalyRule(models.Model):
    _name = 'account.anomaly.rule'
    _description = 'Anomaly Detection Rule'
    _order = 'sequence, name'

    name = fields.Char(string='Rule Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company)

    rule_type = fields.Selection([
        ('amount_threshold', 'Amount Threshold'),
        ('account_type', 'Account Type Pattern'),
        ('partner', 'Partner Rule'),
        ('keyword', 'Description Keyword'),
    ], string='Rule Type', required=True)

    # Amount threshold fields
    min_amount = fields.Float(string='Minimum Amount')
    max_amount = fields.Float(string='Maximum Amount')

    # Account filter
    account_ids = fields.Many2many(
        'account.account', string='Accounts to Monitor')

    # Partner filter
    partner_ids = fields.Many2many(
        'res.partner', string='Partners to Monitor')

    # Keyword matching
    keywords = fields.Char(
        string='Keywords (comma-separated)',
        help='Flag transactions whose narration/reference contains these keywords')

    # Risk assignment
    risk_level = fields.Selection([
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], string='Risk Level', default='medium', required=True)

    alert_title = fields.Char(string='Alert Title Template')
    description_template = fields.Text(string='Alert Description Template')
    score = fields.Integer(string='Anomaly Score', default=50)

    hits_count = fields.Integer(
        string='Total Hits', compute='_compute_hits_count')

    @api.depends()
    def _compute_hits_count(self):
        alert_model = self.env['account.anomaly.alert']
        for rule in self:
            rule.hits_count = alert_model.search_count([
                ('alert_type', '=', 'manual'),
                ('ml_details', 'like', f'rule:{rule.id}'),
            ])
