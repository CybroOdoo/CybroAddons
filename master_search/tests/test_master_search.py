# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestMasterSearch(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestMasterSearch, cls).setUpClass()
        cls.company = cls.env.company
        cls.user = cls.env.user

        # Create res.partner (customers)
        cls.partner_active_1 = cls.env['res.partner'].create({
            'name': 'Test Customer Active 1',
            'email': 'active1@test.com',
            'city': 'New York',
            'zip': '10001',
            'street': 'Broadway',
            'type': 'contact',
            'active': True,
        })
        cls.partner_active_2 = cls.env['res.partner'].create({
            'name': 'Another Client Active 2',
            'email': 'active2@test.com',
            'city': 'Boston',
            'zip': '02108',
            'street': 'Beacon',
            'type': 'contact',
            'active': True,
        })
        cls.partner_inactive = cls.env['res.partner'].create({
            'name': 'Test Customer Inactive',
            'email': 'inactive@test.com',
            'city': 'Chicago',
            'zip': '60601',
            'street': 'Michigan',
            'type': 'contact',
            'active': False,
        })

        # Create products
        cls.product_1 = cls.env['product.template'].create({
            'name': 'Super Widget A',
            'default_code': 'WIDGETA',
            'type': 'consu',
            'active': True,
        })
        cls.product_2 = cls.env['product.template'].create({
            'name': 'Awesome Gadget B',
            'default_code': 'GADGETB',
            'type': 'consu',
            'active': True,
        })
        cls.product_inactive = cls.env['product.template'].create({
            'name': 'Old Antique C',
            'default_code': 'ANTIQUEC',
            'type': 'consu',
            'active': False,
        })

        # Create Sale Order
        pricelist = cls.env['product.pricelist'].search([
            ('company_id', 'in', [cls.company.id, False])
        ], limit=1)
        if not pricelist:
            pricelist = cls.env['product.pricelist'].create({
                'name': 'Test Pricelist',
            })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner_active_1.id,
            'pricelist_id': pricelist.id,
            'picking_policy': 'direct',
            'state': 'draft',
        })

        # Create Purchase Order
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner_active_2.id,
            'state': 'draft',
        })

        # Create Stock Picking (Inventory transaction)
        picking_type = cls.env['stock.picking.type'].search([
            ('company_id', 'in', [cls.company.id, False])
        ], limit=1)
        if not picking_type:
            warehouse = cls.env['stock.warehouse'].search([
                ('company_id', '=', cls.company.id)
            ], limit=1)
            if warehouse:
                picking_type = cls.env['stock.picking.type'].create({
                    'name': 'Test Delivery',
                    'code': 'outgoing',
                    'sequence_code': 'OUT',
                    'warehouse_id': warehouse.id,
                })
        cls.picking = cls.env['stock.picking'].create({
            'partner_id': cls.partner_active_1.id,
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': cls.env.ref('stock.stock_location_stock').id if cls.env.ref('stock.stock_location_stock', raise_if_not_found=False) else cls.env['stock.location'].search([], limit=1).id,
            'location_dest_id': cls.env.ref('stock.stock_location_customers').id if cls.env.ref('stock.stock_location_customers', raise_if_not_found=False) else cls.env['stock.location'].search([], limit=1).id,
        })

        # Create Account Move (Invoice / Journal Entry)
        journal = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id)
        ], limit=1)
        if not journal:
            journal = cls.env['account.journal'].search([
                ('company_id', '=', cls.company.id)
            ], limit=1)
        cls.account_move = cls.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id if journal else False,
            'partner_id': cls.partner_active_2.id,
        })

    def setUp(self):
        super(TestMasterSearch, self).setUp()
        self.env = self.env(context=dict(self.env.context, active_test=False))

    def test_action_search_validation(self):
        """ Test empty search string validation and asterisk bypass """
        search_record = self.env['master.search'].create({
            'search_string': '',
            'search_by': 'any',
        })
        with self.assertRaises(UserError):
            search_record.action_search()

        search_record.search_string = '*'
        search_record.action_search()
        self.assertFalse(search_record.customer_ids)

    def test_action_clear_search(self):
        """ Test clearing search input resets search string and name """
        search_record = self.env['master.search'].create({
            'search_string': 'Test Query',
            'name': 'Test Query',
        })
        search_record.action_clear_search()
        self.assertEqual(search_record.search_string, '')
        self.assertEqual(search_record.name, 'Search')

    def test_action_unlink_search(self):
        """ Test action_unlink_search unlinks the record and returns the action """
        search_record = self.env['master.search'].create({
            'search_string': 'To delete',
        })
        res = search_record.action_unlink_search()
        self.assertFalse(search_record.exists())
        self.assertEqual(res.get('res_model'), 'master.search')

    def test_create_history_limit(self):
        """ Test that creating searches adds to history, and limits user searches to 10 """
        existing = self.env['master.search'].search([
            ('user_id', '=', self.env.user.id)
        ])
        existing.unlink()

        searches = []
        for i in range(12):
            search_rec = self.env['master.search'].create({
                'search_string': 'Query {}'.format(i),
                'user_id': self.env.user.id,
            })
            searches.append(search_rec)

        count = self.env['master.search'].search_count([
            ('user_id', '=', self.env.user.id)
        ])
        self.assertEqual(count, 10)

        self.assertFalse(searches[0].exists())
        self.assertFalse(searches[1].exists())
        self.assertTrue(searches[11].exists())

        last_search = searches[11]
        last_search._get_recent_searches()
        last_search._get_history_count()
        self.assertEqual(last_search.history_count, 10)

    def test_search_by_any(self):
        """ Test search_by = 'any' finds records across different models """
        search_record = self.env['master.search'].create({
            'search_string': 'Active',
            'search_by': 'any',
            'search_mode': 'all',
        })
        search_record.action_search()

        self.assertIn(self.partner_active_1, search_record.customer_ids)
        self.assertIn(self.partner_active_2, search_record.customer_ids)
        self.assertEqual(search_record.customer_count, len(search_record.customer_ids))

        search_record2 = self.env['master.search'].create({
            'search_string': 'Super Widget',
            'search_by': 'any',
            'search_mode': 'all',
        })
        search_record2.action_search()
        self.assertIn(self.product_1, search_record2.product_ids)

    def test_search_match_entire(self):
        """ Test match_entire splits or searches the entire string """
        search_record_split = self.env['master.search'].create({
            'search_string': 'Customer Active',
            'search_by': 'customer',
            'match_entire': False,
            'search_mode': 'all',
        })
        search_record_split.action_search()
        self.assertIn(self.partner_active_1, search_record_split.customer_ids)
        self.assertIn(self.partner_inactive, search_record_split.customer_ids)

        search_record_entire = self.env['master.search'].create({
            'search_string': 'Customer Active',
            'search_by': 'customer',
            'match_entire': True,
            'search_mode': 'all',
        })
        search_record_entire.action_search()
        self.assertIn(self.partner_active_1, search_record_entire.customer_ids)
        self.assertNotIn(self.partner_inactive, search_record_entire.customer_ids)

    def test_search_by_individual_modules(self):
        """ Test searching specifically within individual modules """
        # 1. Customer
        search_cust = self.env['master.search'].create({
            'search_string': 'Boston',
            'search_by': 'customer',
            'search_mode': 'all',
        })
        search_cust.action_search()
        self.assertIn(self.partner_active_2, search_cust.customer_ids)
        self.assertNotIn(self.partner_active_1, search_cust.customer_ids)

        # 2. Product
        search_prod = self.env['master.search'].create({
            'search_string': 'GADGETB',
            'search_by': 'product',
            'search_mode': 'all',
        })
        search_prod.action_search()
        self.assertIn(self.product_2, search_prod.product_ids)
        self.assertNotIn(self.product_1, search_prod.product_ids)

        # 3. Sale
        search_sale = self.env['master.search'].create({
            'search_string': self.sale_order.name,
            'search_by': 'sale details',
            'search_mode': 'all',
        })
        search_sale.action_search()
        self.assertIn(self.sale_order, search_sale.sale_ids)

        # 4. Purchase
        search_purch = self.env['master.search'].create({
            'search_string': 'Client Active 2',
            'search_by': 'purchase details',
            'search_mode': 'all',
        })
        search_purch.action_search()
        self.assertIn(self.purchase_order, search_purch.purchase_ids)

        # 5. Inventory (stock.picking)
        search_inv = self.env['master.search'].create({
            'search_string': self.picking.name,
            'search_by': 'transaction details',
            'search_mode': 'all',
        })
        search_inv.action_search()
        self.assertIn(self.picking, search_inv.transaction_ids)

        # 6. Account (account.move)
        search_acc = self.env['master.search'].create({
            'search_string': 'Client Active 2',
            'search_by': 'account details',
            'search_mode': 'all',
        })
        search_acc.action_search()
        self.assertIn(self.account_move, search_acc.account_ids)

    def test_search_modes(self):
        """ Test that active and inactive search modes correctly filter customer records """
        search_active = self.env['master.search'].create({
            'search_string': 'Test Customer',
            'search_by': 'customer',
            'search_mode': 'active',
        })
        search_active.action_search()
        self.assertIn(self.partner_active_1, search_active.customer_ids)
        self.assertNotIn(self.partner_inactive, search_active.customer_ids)

        search_inactive = self.env['master.search'].create({
            'search_string': 'Test Customer',
            'search_by': 'customer',
            'search_mode': 'inactive',
        })
        search_inactive.action_search()
        self.assertNotIn(self.partner_active_1, search_inactive.customer_ids)
        self.assertIn(self.partner_inactive, search_inactive.customer_ids)
