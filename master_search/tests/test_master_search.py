# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav P P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestMasterSearch(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner_active = cls.env['res.partner'].create({
            'name': 'Searchable Active Partner',
            'type': 'contact',
            'email': 'active_search@example.com',
            'active': True,
        })
        cls.partner_inactive = cls.env['res.partner'].create({
            'name': 'Searchable Inactive Partner',
            'type': 'contact',
            'email': 'inactive_search@example.com',
            'active': False,
        })

        cls.product_active = cls.env['product.template'].create({
            'name': 'Searchable Active Product',
            'type': 'consu',
            'active': True,
        })
        cls.product_inactive = cls.env['product.template'].create({
            'name': 'Searchable Inactive Product',
            'type': 'consu',
            'active': False,
        })

        picking_type = cls.env['stock.picking.type'].search([
            ('company_id', '=', cls.env.company.id)
        ], limit=1)

        location = cls.env['stock.location'].search([
            ('company_id', 'in', [cls.env.company.id, False])
        ], limit=1)

        cls.stock_picking = cls.env['stock.picking'].create({
            'name': 'WH/OUT/0001',
            'partner_id': cls.partner_active.id,
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': location.id if location else False,
            'location_dest_id': location.id if location else False,
        })

        cls.sale_order = cls.env['sale.order'].create({
            'name': 'SO/2026/0001',
            'partner_id': cls.partner_active.id,
        })

        cls.purchase_order = cls.env['purchase.order'].create({
            'name': 'PO/2026/0001',
            'partner_id': cls.partner_active.id,
        })

        journal = cls.env['account.journal'].search([
            ('company_id', '=', cls.env.company.id)
        ], limit=1)
        cls.account_move = cls.env['account.move'].create({
            'name': 'INV/2026/0001',
            'partner_id': cls.partner_active.id,
            'move_type': 'entry',
            'journal_id': journal.id if journal else False,
        })

        cls.env.flush_all()

    def test_search_empty(self):
        """Test search with empty search string raises UserError."""
        search_record = self.env['master.search'].create({
            'search_string': '',
        })
        with self.assertRaises(UserError):
            search_record.action_search()

    def test_search_asterisk(self):
        """Test search with '*' in search string does nothing/returns early."""
        search_record = self.env['master.search'].create({
            'search_string': 'test*',
        })
        search_record.action_search()
        self.assertFalse(search_record.customer_ids)

    def test_clear_search(self):
        """Test action_clear_search resets search string and name."""
        search_record = self.env['master.search'].create({
            'search_string': 'some search',
            'name': 'some search',
        })
        search_record.action_clear_search()
        self.assertEqual(search_record.search_string, '')
        self.assertEqual(search_record.name, 'Search')

    def test_unlink_search(self):
        """Test action_unlink_search unlinks record and returns action dictionary."""
        search_record = self.env['master.search'].create({
            'search_string': 'search to delete',
        })
        res_id = search_record.id
        action = search_record.action_unlink_search()
        self.assertTrue(isinstance(action, dict))
        self.assertEqual(action.get('res_model'), 'master.search')
        deleted_record = self.env['master.search'].search([('id', '=', res_id)])
        self.assertFalse(deleted_record)

    def test_recent_searches_limit(self):
        """Test that history count is updated and oldest search is unlinked if count > 10."""
        # Unlink any existing master.search records for this user first
        self.env['master.search'].search([('user_id', '=', self.env.user.id)]).unlink()

        searches = []
        for i in range(11):
            search_record = self.env['master.search'].create({
                'search_string': f'Search {i}',
            })
            searches.append(search_record)

        count = self.env['master.search'].search_count([('user_id', '=', self.env.user.id)])
        self.assertEqual(count, 10)

        first_search = self.env['master.search'].search([('id', '=', searches[0].id)])
        self.assertFalse(first_search)

        last_search = self.env['master.search'].search([('id', '=', searches[-1].id)])
        self.assertTrue(last_search)

        last_search._get_recent_searches()
        last_search._get_history_count()
        self.assertGreater(last_search.history_count, 0)

    def test_search_by_any(self):
        """Test searching with search_by='any' finds records in various models."""
        search_record = self.env['master.search'].create({
            'search_string': 'Searchable',
            'search_by': 'any',
            'search_mode': 'all',
        })
        search_record.action_search()

        customers = search_record.with_context(active_test=False).customer_ids
        products = search_record.with_context(active_test=False).product_ids

        self.assertIn(self.partner_active, customers)
        self.assertIn(self.partner_inactive, customers)
        self.assertIn(self.product_active, products)
        self.assertIn(self.product_inactive, products)

    def test_search_by_customer(self):
        """Test searching with search_by='customer' only matches partners."""
        search_record = self.env['master.search'].create({
            'search_string': 'Searchable',
            'search_by': 'customer',
            'search_mode': 'all',
        })
        search_record.action_search()

        customers = search_record.with_context(active_test=False).customer_ids
        products = search_record.with_context(active_test=False).product_ids

        self.assertIn(self.partner_active, customers)
        self.assertFalse(products)

        search_record_active = self.env['master.search'].create({
            'search_string': 'Searchable',
            'search_by': 'customer',
            'search_mode': 'active',
        })
        search_record_active.action_search()
        self.assertIn(self.partner_active, search_record_active.customer_ids)
        self.assertNotIn(self.partner_inactive, search_record_active.with_context(active_test=False).customer_ids)

        search_record_inactive = self.env['master.search'].create({
            'search_string': 'Searchable',
            'search_by': 'customer',
            'search_mode': 'inactive',
        })
        search_record_inactive.action_search()
        self.assertNotIn(self.partner_active, search_record_inactive.with_context(active_test=False).customer_ids)
        self.assertIn(self.partner_inactive, search_record_inactive.with_context(active_test=False).customer_ids)

    def test_search_by_product(self):
        """Test searching with search_by='product' only matches products."""
        search_record = self.env['master.search'].create({
            'search_string': 'Searchable',
            'search_by': 'product',
        })
        search_record.action_search()
        self.assertFalse(search_record.customer_ids)
        self.assertIn(self.product_active, search_record.product_ids)

    def test_search_by_sale_details(self):
        """Test searching with search_by='sale details' matches sale orders."""
        search_record = self.env['master.search'].create({
            'search_string': self.sale_order.name,
            'search_by': 'sale details',
        })
        search_record.action_search()
        self.assertIn(self.sale_order, search_record.sale_ids)

    def test_search_by_purchase_details(self):
        """Test searching with search_by='purchase details' matches purchase orders."""
        search_record = self.env['master.search'].create({
            'search_string': self.purchase_order.name,
            'search_by': 'purchase details',
        })
        search_record.action_search()
        self.assertIn(self.purchase_order, search_record.purchase_ids)

    def test_search_by_transaction_details(self):
        """Test searching with search_by='transaction details' matches stock pickings."""
        search_record = self.env['master.search'].create({
            'search_string': self.stock_picking.name,
            'search_by': 'transaction details',
        })
        search_record.action_search()
        self.assertIn(self.stock_picking, search_record.transaction_ids)

    def test_search_by_account_details(self):
        """Test searching with search_by='account details' matches account moves."""
        search_record = self.env['master.search'].create({
            'search_string': self.account_move.name,
            'search_by': 'account details',
        })
        search_record.action_search()
        self.assertIn(self.account_move, search_record.account_ids)

    def test_match_entire_sentence(self):
        """Test that match_entire=True searches for the whole string, while False searches for separate keys."""
        product = self.env['product.template'].create({
            'name': 'Unique Green Banana',
            'type': 'consu',
        })
        self.env.flush_all()

        search_split = self.env['master.search'].create({
            'search_string': 'Banana Green',
            'search_by': 'product',
            'match_entire': False,
        })
        search_split.action_search()
        self.assertIn(product, search_split.product_ids)

        search_entire = self.env['master.search'].create({
            'search_string': 'Banana Green',
            'search_by': 'product',
            'match_entire': True,
        })
        search_entire.action_search()
        self.assertNotIn(product, search_entire.product_ids)

    def test_computed_counts(self):
        """Test computed count fields for various related models."""
        search_record = self.env['master.search'].create({
            'search_string': 'Test',
        })

        search_record.customer_ids = [(6, 0, [self.partner_active.id])]
        search_record.product_ids = [(6, 0, [self.product_active.id])]
        search_record.transaction_ids = [(6, 0, [self.stock_picking.id])]
        search_record.sale_ids = [(6, 0, [self.sale_order.id])]
        search_record.purchase_ids = [(6, 0, [self.purchase_order.id])]
        search_record.account_ids = [(6, 0, [self.account_move.id])]

        search_record._get_operator_count()
        search_record._get_product_count()
        search_record._get_transaction_count()
        search_record._get_sale_count()
        search_record._get_purchase_count()
        search_record._get_account_count()

        self.assertEqual(search_record.customer_count, 1)
        self.assertEqual(search_record.product_count, 1)
        self.assertEqual(search_record.transaction_count, 1)
        self.assertEqual(search_record.sale_count, 1)
        self.assertEqual(search_record.purchase_count, 1)
        self.assertEqual(search_record.account_count, 1)
