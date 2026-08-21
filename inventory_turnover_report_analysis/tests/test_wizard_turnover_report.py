# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import io
from types import SimpleNamespace
from unittest.mock import Mock

from odoo.tests.common import TransactionCase

from odoo.addons.inventory_turnover_report_analysis.wizard.turnover_report import (
    TurnoverReport,
)


class TestTurnoverReport(TransactionCase):
    def setUp(self):
        super().setUp()
        self.report = TurnoverReport

    def _make_report(self, **attrs):
        return SimpleNamespace(**attrs)

    def _make_env(self, mapping):
        class FakeEnv:
            def __getitem__(self, model_name):
                return mapping[model_name]

        return FakeEnv()

    def test_default_category_ids_uses_first_product_category(self):
        category = SimpleNamespace(id=42)
        product = SimpleNamespace(product_tmpl_id=SimpleNamespace(categ_id=category))
        report = self._make_report(
            env=self._make_env({
                'product.product': SimpleNamespace(
                    search=Mock(return_value=product),
                )
            })
        )

        result = TurnoverReport._default_categ_ids(report)

        self.assertEqual(result, [(6, 0, [42])])

    def test_default_warehouse_ids_uses_first_warehouse(self):
        warehouse = SimpleNamespace(id=17)
        report = self._make_report(
            env=self._make_env({
                'stock.warehouse': SimpleNamespace(
                    search=Mock(return_value=warehouse),
                )
            })
        )

        result = TurnoverReport._default_warehouse_ids(report)

        self.assertEqual(result, [(6, 0, [17])])

    def test_date_comparison_merges_and_filters_by_range(self):
        report = self._make_report(
            start_date="2026-06-01",
            end_date="2026-06-30",
        )
        data = [
            {
                'id': 1,
                'last_count_date': "2026-06-10",
                'opening_stock': 2,
                'closing_stock': 4,
            },
            {
                'id': 1,
                'last_count_date': "2026-06-10",
                'opening_stock': 3,
                'closing_stock': 5,
            },
            {
                'id': 2,
                'last_count_date': "2026-07-01",
                'opening_stock': 1,
                'closing_stock': 1,
            },
        ]

        result = TurnoverReport._date_comparison(report, data)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['id'], 1)
        self.assertEqual(result[0]['opening_stock'], 5)
        self.assertEqual(result[0]['closing_stock'], 9)

    def test_action_xlsx_report_generate_returns_report_payload(self):
        report = self._make_report(
            start_date="2026-06-01",
            end_date="2026-06-30",
            call_render_report=Mock(return_value=[{'product': 'A'}]),
        )
        report.env = Mock()

        result = TurnoverReport.action_xlsx_report_generate(report)

        self.assertEqual(result['type'], 'ir.actions.report')
        self.assertEqual(result['report_type'], 'xlsx')
        self.assertEqual(result['data']['report_name'], 'Inventory Turnover Analysis Report')

    def test_action_pdf_report_generate_uses_report_action(self):
        report_action = Mock(return_value={'type': 'ir.actions.report'})
        report = self._make_report(
            start_date="2026-06-01",
            end_date="2026-06-30",
            call_render_report=Mock(return_value=[{'product': 'A'}]),
            env=self._make_env({
                'ir.actions.report': SimpleNamespace(report_action=report_action),
            }),
        )
        report.env.ref = Mock(return_value=SimpleNamespace(report_action=report_action))

        result = TurnoverReport.action_pdf_report_generate(report)

        self.assertEqual(result, {'type': 'ir.actions.report'})
        report.env.ref.assert_called_once_with(
            'inventory_turnover_report_analysis.inventory_turnover_report'
        )
        report_action.assert_called_once()

    def test_get_xlsx_report_writes_to_response_stream(self):
        report = self._make_report()
        response = SimpleNamespace(stream=SimpleNamespace(write=Mock()))
        data = {
            'stock_report': [
                {
                    'product': 'Test Product',
                    'opening_stock': 1,
                    'closing_stock': 2,
                    'average_stock': 1.5,
                    'sale_count': 3,
                    'purchase_count': 4,
                    'turnover_ratio': 2.0,
                }
            ],
            'start_date': "2026-06-01",
            'end_date': "2026-06-30",
        }

        TurnoverReport.get_xlsx_report(report, data, response)

        self.assertTrue(response.stream.write.called)
        written = response.stream.write.call_args.args[0]
        self.assertIsInstance(written, (bytes, bytearray))
        self.assertGreater(len(written), 0)

    def test_action_data_fetch_creates_fetch_records(self):
        created = []
        fetch_model = SimpleNamespace(
            search=Mock(return_value=SimpleNamespace(unlink=Mock())),
            create=Mock(side_effect=lambda vals: created.append(vals)),
        )
        report = self._make_report(
            call_render_model=Mock(return_value=[
                {
                    'company_id': 1,
                    'warehouse_id': 2,
                    'id': 3,
                    'category_id': 4,
                    'opening_stock': 5,
                    'closing_stock': 6,
                    'average_stock': 7,
                    'sale_count': 8,
                    'purchase_count': 9,
                    'turnover_ratio': 10,
                }
            ]),
            env=self._make_env({'fetch.data': fetch_model}),
        )

        result = TurnoverReport.action_data_fetch(report)

        self.assertEqual(result['res_model'], 'fetch.data')
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0]['product_id'], 3)
        fetch_model.create.assert_called_once()

    def test_action_generate_graph_view_creates_graph_records(self):
        created = []
        graph_model = SimpleNamespace(
            search=Mock(return_value=SimpleNamespace(unlink=Mock())),
            create=Mock(side_effect=lambda vals: created.append(vals)),
        )
        report = self._make_report(
            call_render_model=Mock(return_value=[
                {
                    'company_id': 1,
                    'warehouse_id': 2,
                    'id': 3,
                    'category_id': 4,
                    'opening_stock': 5,
                    'closing_stock': 6,
                    'average_stock': 7,
                    'sale_count': 8,
                    'purchase_count': 9,
                    'turnover_ratio': 10,
                }
            ]),
            env=self._make_env({'turnover.graph.analysis': graph_model}),
        )

        result = TurnoverReport.action_generate_graph_view(report)

        self.assertEqual(result['view_mode'], 'graph')
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0]['product_id'], 3)
        graph_model.create.assert_called_once()

    def test_call_render_report_delegates_to_date_comparison(self):
        quant = SimpleNamespace(
            product_id=SimpleNamespace(
                id=10,
                sales_count=4,
                purchased_product_qty=2,
                categ_id=SimpleNamespace(complete_name='All / Cat'),
                display_name='[10] Product',
            ),
            location_id=SimpleNamespace(
                usage='internal',
                warehouse_id=SimpleNamespace(name='Main WH'),
            ),
            available_quantity=6,
            quantity=8,
            last_count_date='2026-06-10',
            company_id=SimpleNamespace(name='My Company'),
        )
        report = self._make_report(
            product_ids=SimpleNamespace(ids=[10]),
            company_ids=SimpleNamespace(ids=[1]),
            category_ids=SimpleNamespace(ids=[2]),
            warehouse_ids=[],
            env=self._make_env({
                'stock.quant': SimpleNamespace(search=Mock(return_value=[quant])),
            }),
            _date_comparison=Mock(return_value=['sentinel']),
        )

        result = TurnoverReport.call_render_report(report)

        self.assertEqual(result, ['sentinel'])
        report._date_comparison.assert_called_once()

    def test_call_render_model_delegates_to_date_comparison(self):
        quant = SimpleNamespace(
            product_id=SimpleNamespace(
                id=10,
                sales_count=4,
                purchased_product_qty=2,
                categ_id=SimpleNamespace(id=99),
                display_name='[10] Product',
            ),
            location_id=SimpleNamespace(
                usage='internal',
                warehouse_id=SimpleNamespace(id=7),
            ),
            available_quantity=6,
            quantity=8,
            last_count_date='2026-06-10',
            company_id=SimpleNamespace(id=1),
        )
        report = self._make_report(
            product_ids=SimpleNamespace(ids=[10]),
            company_ids=SimpleNamespace(ids=[1]),
            category_ids=SimpleNamespace(ids=[2]),
            warehouse_ids=[],
            env=self._make_env({
                'stock.quant': SimpleNamespace(search=Mock(return_value=[quant])),
            }),
            _date_comparison=Mock(return_value=['sentinel']),
        )

        result = TurnoverReport.call_render_model(report)

        self.assertEqual(result, ['sentinel'])
        report._date_comparison.assert_called_once()
