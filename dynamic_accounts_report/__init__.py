# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from . import controllers
from . import wizard
from . import report
from . import models
from odoo import api, SUPERUSER_ID


def _load_account_details_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for record in env['account.financial.report'].search(
            [('type', '=', 'account_type')]):
        if record.get_metadata()[0].get(
                'xmlid') == 'base_accounting_kit.account_financial_report_other_income0':
            for rec in env['account.account'].search(
                    [('account_type', '=', 'income_other')]):
                record.write({"account_ids": [(4, rec.id)]})
        elif record.get_metadata()[0].get(
                'xmlid') == 'base_accounting_kit.financial_report_cost_of_revenue':
            for rec in env['account.account'].search(
                    [('account_type', '=', 'expense_direct_cost')]):
                record.write({"account_ids": [(4, rec.id)]})
        elif record.get_metadata()[0].get(
                'xmlid') == 'base_accounting_kit.account_financial_report_operating_income0':
            for rec in env['account.account'].search(
                    [('account_type', 'in', ('equity_unaffected', 'income'))]):
                record.write({"account_ids": [(4, rec.id)]})
        elif record.get_metadata()[0].get(
                'xmlid') == 'base_accounting_kit.account_financial_report_expense0':
            for rec in env['account.account'].search(
                    [('account_type', 'in',
                      ('expense', 'expense_depreciation'))]):
                record.write({"account_ids": [(4, rec.id)]})
        elif record.get_metadata()[0].get(
                'xmlid') == 'base_accounting_kit.account_financial_report_assets0':
            for rec in env['account.account'].search(
                    [('account_type', 'in', (
                            'asset_receivable', 'asset_non_current',
                            'asset_current',
                            'asset_prepayments', 'asset_fixed',
                            'asset_cash'))]):
                record.write({"account_ids": [(4, rec.id)]})
        elif record.get_metadata()[0].get(
                'xmlid') == 'base_accounting_kit.account_financial_report_liability0':
            for rec in env['account.account'].search(
                    [('account_type', 'in', (
                            'liability_payable', 'equity',
                            'liability_current',
                            'liability_non_current',
                            'liability_credit_card'))]):
                record.write({"account_ids": [(4, rec.id)]})


def unlink_records_financial_report(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for record in env['account.financial.report'].search(
            [('type', '=', 'account_type')]):
        record.write({"account_ids": [(5, 0, 0)]})
