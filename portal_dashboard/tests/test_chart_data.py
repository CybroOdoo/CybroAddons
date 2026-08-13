# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (https://www.cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestChartData(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Portal Partner',
        })
        cls.user = cls.env['res.users'].create({
            'name': 'Test Portal User',
            'login': 'portal_user_test',
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
            'partner_id': cls.partner.id,
        })
        
        # Test requires account move data
        income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.env.company.id)
        ], limit=1)
        if not income_account:
            income_account = cls.env['account.account'].create({
                'name': 'Test Income Account',
                'code': 'TESTINC',
                'account_type': 'income',
                'company_ids': [(4, cls.env.company.id)],
            })

        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': '2030-01-01',
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Test service',
                    'quantity': 1.0,
                    'price_unit': 100.0,
                    'account_id': income_account.id,
                })
            ],
        })
        cls.invoice.action_post()

        # Test requires sale order data
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.user.id,
            'state': 'sale',
        })

        cls.quotation = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.user.id,
            'state': 'sent',
        })

        # Test requires purchase order data
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.user.id,
            'state': 'purchase',
        })

        cls.rfq = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
            'user_id': cls.user.id,
            'state': 'sent',
        })

    def test_datafetch(self):
        """Test the datafetch method to ensure it correctly aggregates data."""
        chart_data_model = self.env['portal.dashboard.data'].with_user(self.user)
        result = chart_data_model.datafetch()

        # Check returned dictionary keys
        self.assertIn('target', result)
        self.assertIn('target_po', result)
        self.assertIn('target_accounting', result)

        self.assertEqual(len(result['target']), 2, 'target array should have 2 elements')
        self.assertEqual(len(result['target_po']), 2, 'target_po array should have 2 elements')
        self.assertEqual(len(result['target_accounting']), 1, 'target_accounting array should have 1 element')
        
        # Our target array structure based on datafetch returns.
        self.assertTrue(result['target'][0] >= 1, 'Sale order count should be >= 1')
        self.assertTrue(result['target'][1] >= 1, 'Quotation count should be >= 1')
        self.assertTrue(result['target_po'][0] >= 1, 'PO count should be >= 1')
        self.assertTrue(result['target_po'][1] >= 1, 'RFQ count should be >= 1')
        self.assertTrue(result['target_accounting'][0] >= 1, 'Invoice count should be >= 1')
