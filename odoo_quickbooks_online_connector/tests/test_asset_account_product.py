# -*- coding: utf-8 -*-

from unittest.mock import Mock, patch

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAssetAccountProductWizard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.quickbooks = cls.env['quickbooks.connector'].create({
            'name': 'Test QuickBooks Connection',
            'quickbooks_realm': '1234567890',
            'quickbooks_client': 'client-id',
            'quickbooks_client_secret': 'client-secret',
            'quickbooks_access_token': 'access-token',
            'quickbooks_api_url': 'https://example.com/v3/company/',
            'authorised': True,
        })

        cls.asset_account = cls.env['account.account'].create({
            'name': 'Test Asset Account',
            'code': 'TAS100',
            'account_type': 'asset_current',
        })
        cls.income_account = cls.env['account.account'].create({
            'name': 'Test Income Account',
            'code': 'TIN100',
            'account_type': 'income',
        })
        cls.expense_account = cls.env['account.account'].create({
            'name': 'Test Expense Account',
            'code': 'TEX100',
            'account_type': 'expense',
        })
        cls.category = cls.env['product.category'].create({
            'name': 'Test Product Category',
            'property_account_income_categ_id': cls.income_account.id,
            'property_account_expense_categ_id': cls.expense_account.id,
        })
        cls.product = cls.env['product.template'].create({
            'name': 'QuickBooks Test Product',
            'list_price': 42.0,
            'standard_price': 21.0,
            'type': 'service',
            'description_sale': 'Sale description',
            'description_purchase': 'Purchase description',
            'categ_id': cls.category.id,
        }).product_variant_id

    def _wizard(self):
        return self.env['asset.account.product'].create({
            'account_type_id': self.asset_account.id,
        })

    def test_get_import_query_returns_request_payload(self):
        wizard = self._wizard()

        result = wizard.get_import_query()

        self.assertEqual(result['url'], 'https://example.com/v3/company/1234567890')
        self.assertEqual(result['headers']['Authorization'], 'Bearer access-token')
        self.assertEqual(result['headers']['Accept'], 'application/json')
        self.assertEqual(result['headers']['Content-Type'], 'text/plain')

    def test_action_export_products_skips_already_linked_products(self):
        wizard = self._wizard()
        self.product.write({'qbooks_product': 'QBO-ITEM-1'})
        wizard.write({'product_ids': [(6, 0, self.product.ids)]})

        with patch.object(type(wizard), 'get_import_query', return_value={
            'url': 'https://example.com/v3/company/1234567890',
            'headers': {'Authorization': 'Bearer access-token'},
        }), patch.object(type(wizard), 'create_product_data') as create_mock:
            action = wizard.action_export_products()

        create_mock.assert_not_called()
        self.assertIsNone(action)

    def test_action_export_products_exports_unlinked_product(self):
        wizard = self._wizard()
        self.product.write({'qbooks_product': False})
        wizard.write({'product_ids': [(6, 0, self.product.ids)]})

        with patch.object(type(wizard), 'get_import_query', return_value={
            'url': 'https://example.com/v3/company/1234567890',
            'headers': {'Authorization': 'Bearer access-token'},
        }), patch.object(type(wizard), 'create_product_data') as create_mock:
            action = wizard.action_export_products()

        create_mock.assert_called_once()
        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['message'], '1 products exported')

    def test_create_product_data_writes_qbooks_fields_from_response(self):
        wizard = self._wizard()
        response = Mock()
        response.json.return_value = {
            'Item': {
                'Id': '9001',
                'SyncToken': '7',
            }
        }

        with patch('odoo.addons.odoo_quickbooks_online_connector.wizard.asset_account_product.requests.post',
                   return_value=response) as post_mock:
            wizard.create_product_data(
                self.product,
                'https://example.com/v3/company/1234567890/item?minorversion=40',
                {'Authorization': 'Bearer access-token'},
            )

        post_mock.assert_called_once()
        self.assertEqual(self.product.qbooks_product, '9001')
        self.assertEqual(self.product.qbooks_sync_token, '7')
