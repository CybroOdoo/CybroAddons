# -*- coding: utf-8 -*-
#############################################################################
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

from odoo import fields, models

class OilAroTemplate(models.Model):
    _name = 'oil.aro.template'
    _description = 'ARO Configuration Template'
    _rec_name = 'name'

    name = fields.Char(string='Template Name', required=True, help="A unique name or reference identifier used to track this record in the system.")
    active = fields.Boolean(default=True, help="Uncheck this field to archive the record without permanently deleting it.")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, help="The company managing this operational record or transaction.")

    # ─────────────────────────────────────────
    # ACCOUNTING
    # ─────────────────────────────────────────

    aro_asset_account_id = fields.Many2one('account.account', string='ARO Asset Account', required=True,
                                           domain="[('account_type', '=', 'asset_non_current')]",
                                           help="Link this transaction or record to the corresponding 'aro asset account' reference.")
    liability_account_id = fields.Many2one('account.account', string='ARO Liability Account', required=True,
                                           domain="[('account_type', '=', 'liability_non_current')]",
                                           help="Link this transaction or record to the corresponding 'aro liability account' reference.")
    accretion_expense_account_id = fields.Many2one('account.account', string='Accretion Expense Account',
                                                   required=True, domain="[('account_type', '=', 'expense')]",
                                                   help="Link this transaction or record to the corresponding 'accretion expense account' reference.", )
    wip_account_id = fields.Many2one('account.account', string='Decommissioning WIP Account', required=True,
                                     domain="[('account_type', '=', 'asset_current')]",
                                     help="Link this transaction or record to the corresponding 'decommissioning wip account' reference.")
    settlement_gain_account_id = fields.Many2one('account.account', string='Settlement Gain Account',
                                                 domain="[('account_type', '=', 'income_other')]",
                                                 help="Link this transaction or record to the corresponding 'settlement gain account' reference.")
    settlement_loss_account_id = fields.Many2one('account.account', string='Settlement Loss Account',
                                                 domain="[('account_type', '=', 'expense')]",
                                                 help="Link this transaction or record to the corresponding 'settlement loss account' reference.")
    deferred_tax_asset_account_id = fields.Many2one('account.account', string='Deferred Tax Asset ARO Account',
                                                    domain="[('account_type', '=', 'asset_non_current')]",
                                                    help="Deferred tax asset account for ARO.")
    deferred_tax_benefit_account_id = fields.Many2one('account.account', string='Deferred Tax Benefit Account',
                                                      domain="[('account_type', '=', 'expense')]",
                                                      help="Deferred tax benefit account for ARO.")
    journal_id = fields.Many2one('account.journal', string='ARO Journal', domain=[('type', '=', 'general')],
                                 required=True, help="Link this transaction or record to the corresponding 'aro journal' reference.")

    # ─────────────────────────────────────────
    # DEFAULT PARAMETERS
    # ─────────────────────────────────────────

    discount_rate = fields.Monetary(string='Default Discount Rate (%)', default=6.0, help="Specify the numerical measurement, volume, or financial amount for 'default discount rate (%)'.", )

    accretion_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'),
                                            ('annual', 'Annual'), ], string='Default Accretion Frequency',
                                           default='quarterly', help="Select the appropriate classification or category for 'default accretion frequency'.", )
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id, help="Link this transaction or record to the corresponding 'currency' reference.")
