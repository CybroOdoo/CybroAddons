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

class TestReports(TransactionCase):
    def setUp(self):
        super(TestReports, self).setUp()
        self.product = self.env['product.product'].create({
            'name': 'Test Report Product',
            'type': 'consu', 'is_storable': True
        })
        self.inventory_pdf_report = self.env['report.all_in_one_inventory_kit.inventory_pdf_report']
        self.product_stock_report = self.env['report.all_in_one_inventory_kit.report_product_stock_template']

    def test_inventory_pdf_report(self):
        # test _get_report_values
        data = {
            'report_data': {
                'report_lines': [{'name': 'Test Line'}],
                'filters': {'report_type': 'Report By Transfers'}
            }
        }
        res = self.inventory_pdf_report.with_context(inventory_pdf_report=True)._get_report_values([], data)
        self.assertEqual(res['report_main_line_data'][0]['name'], 'Test Line')
        self.assertEqual(res['Filters']['report_type'], 'Report By Transfers')
        self.assertEqual(res['company'], self.env.company)

    def test_product_stock_report(self):
        # test _get_report_values
        res = self.product_stock_report.with_context(active_ids=[self.product.id])._get_report_values([], {})
        self.assertEqual(res['doc_ids'], [self.product.id])
        self.assertEqual(res['doc_model'], 'product.product')
        self.assertEqual(res['docs'][0], self.product)
        self.assertEqual(res['res_company'], self.env.company)
