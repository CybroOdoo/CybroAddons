# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
###############################################################################

from odoo.tests.common import TransactionCase
import json

class TestWizardStockHistory(TransactionCase):
    def setUp(self):
        super(TestWizardStockHistory, self).setUp()
        self.warehouse = self.env['stock.warehouse'].search([], limit=1)
        self.category = self.env['product.category'].create({'name': 'Test Category'})
        self.product = self.env['product.product'].create({
            'name': 'Test Stock Product',
            'type': 'consu', 'is_storable': True,
            'categ_id': self.category.id,
            'standard_price': 50.0,
        })
        
        self.wizard = self.env['wizard.stock.history'].create({
            'warehouse_ids': [(6, 0, [self.warehouse.id])],
            'category_ids': [(6, 0, [self.category.id])],
        })

    def test_action_export_xlsx(self):
        res = self.wizard.action_export_xlsx()
        self.assertEqual(res['type'], 'ir.actions.report')
        self.assertEqual(res['report_type'], 'stock_xlsx')
        data = json.loads(res['data']['options'])
        self.assertEqual(data['model'], 'wizard.stock.history')
        self.assertIn(self.warehouse.id, data['warehouse'])
        self.assertIn(self.category.id, data['category'])

    def test_get_warehouse(self):
        # get_warehouse expects the recordset `data` to have warehouse_ids
        wh_names, wh_ids = self.wizard.get_warehouse(self.wizard)
        self.assertIn(self.warehouse.name, wh_names)
        self.assertIn(self.warehouse.id, wh_ids)

    def test_get_lines(self):
        # test get_lines method
        lines = self.wizard.get_lines(self.wizard.category_ids, self.warehouse.id)
        self.assertTrue(isinstance(lines, list))
        # Find the line for our test product
        found = False
        for line in lines:
            if line['name'] == self.product.name:
                found = True
                self.assertEqual(line['category'], self.category.name)
                self.assertEqual(line['cost_price'], 50.0)
        self.assertTrue(found)
