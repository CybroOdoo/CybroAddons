# -*- coding: utf-8 -*-
"""Shared fixtures for base_accounting_kit tests.

Built on ``AccountTestInvoicingCommon`` which provides a company with a chart
of accounts, journals (sale/purchase/bank/cash/misc), accounts, partners and
products, plus the ``init_invoice`` helper.
"""
from odoo import Command, fields
from odoo.tests import Form
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class AccountKitCommon(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.misc_journal = cls.company_data['default_journal_misc']
        # Create a fresh bank journal so the account.journal create-override
        # links the PDC payment-method lines (the production path for new
        # bank journals). The install-time company journal predates the module.
        cls.bank_journal = cls.env['account.journal'].create({
            'name': 'Test Bank', 'type': 'bank', 'code': 'TBNKK',
        })
        cls.asset_account = cls.company_data['default_account_assets']
        cls.expense_account = cls.company_data['default_account_expense']

        # An asset category usable by the whole asset test-suite.
        cls.asset_category = cls.env['account.asset.category'].create({
            'name': 'Vehicles',
            'company_id': cls.env.company.id,
            'price': 1200.0,
            'account_asset_id': cls.asset_account.id,
            'account_depreciation_id': cls.asset_account.id,
            'account_depreciation_expense_id': cls.expense_account.id,
            'account_disposal_id': cls.expense_account.id,
            'journal_id': cls.misc_journal.id,
            'method': 'linear',
            'method_number': 4,
            'method_period': 12,
            'method_time': 'number',
            'type': 'purchase',
        })

    @classmethod
    def _create_asset(cls, value=1200.0, open_asset=False, method_number=4,
                      method_period=12, date='2020-01-01'):
        """Create an asset via Form so the category onchange fills accounts."""
        form = Form(cls.env['account.asset.asset'])
        form.name = 'Test Asset'
        form.category_id = cls.asset_category
        form.value = value
        form.method_number = method_number
        form.method_period = method_period
        form.date = fields.Date.to_date(date)
        asset = form.save()
        asset.open_asset = open_asset
        return asset
