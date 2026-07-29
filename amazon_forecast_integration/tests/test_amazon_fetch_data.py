# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

import csv
from types import SimpleNamespace
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.addons.amazon_forecast_integration.models import amazon_fetch_data


@tagged('-at_install', 'post_install')
class TestAmazonFetchData(TransactionCase):
    def test_action_fetch_data_exports_stock_moves_to_csv(self):
        with NamedTemporaryFile(suffix='.csv') as csv_file:
            fetch_data = self.env['amazon.fetch.data'].create({
                'url': 'http://example.test',
                'db_name': 'test_db',
                'db_username': 'admin',
                'db_password': 'admin',
                'csv_file_path': csv_file.name,
            })
            common_proxy = MagicMock()
            common_proxy.authenticate.return_value = 7
            object_proxy = MagicMock()
            object_proxy.execute_kw.return_value = [{
                'product_id': [1, 'Product A'],
                'date': '2026-01-01 00:00:00',
                'product_uom_qty': 5.0,
                'id': 10,
                'reference': 'WH/OUT/0001',
                'location_id': [2, 'Stock'],
                'location_dest_id': [3, 'Customers'],
                'origin': 'SO001',
            }]

            xmlrpc_client = SimpleNamespace(
                ServerProxy=MagicMock(
                    side_effect=[common_proxy, object_proxy]))
            with patch.object(
                amazon_fetch_data.xmlrpc.client,
                'client',
                xmlrpc_client,
                create=True,
            ), patch.object(
                amazon_fetch_data.xmlrpc.client,
                'ServerProxy',
                MagicMock(return_value=object_proxy),
            ):
                action = fetch_data.action_fetch_data()

            self.assertEqual(action['res_model'], 'amazon.bucket')
            self.assertEqual(action['view_mode'], 'form')
            object_proxy.execute_kw.assert_called_once()
            csv_file.seek(0)
            rows = list(csv.DictReader(
                line.decode() for line in csv_file.readlines()))

        self.assertEqual(rows, [{
            'item_id': 'Product A',
            'timestamp': '2026-01-01 00:00:00',
            'demand': '5.0',
            'id': '10',
            'reference': 'WH/OUT/0001',
            'location_id': 'Stock',
            'location_dest_id': 'Customers',
            'origin': 'SO001',
        }])

    def test_action_fetch_data_converts_oserror_to_validation_error(self):
        fetch_data = self.env['amazon.fetch.data'].create({
            'url': 'http://example.test',
            'db_name': 'test_db',
            'db_username': 'admin',
            'db_password': 'admin',
            'csv_file_path': '/tmp/forecast.csv',
        })

        xmlrpc_client = SimpleNamespace(
            ServerProxy=MagicMock(side_effect=OSError))
        with patch.object(
            amazon_fetch_data.xmlrpc.client,
            'client',
            xmlrpc_client,
            create=True,
        ), self.assertRaises(ValidationError):
            fetch_data.action_fetch_data()

    def test_get_file_path_returns_first_configured_path(self):
        fetch_data = self.env['amazon.fetch.data'].create({
            'url': 'http://example.test',
            'db_name': 'test_db',
            'db_username': 'admin',
            'db_password': 'admin',
            'csv_file_path': '/tmp/forecast.csv',
        })

        self.assertEqual(fetch_data.get_file_path(), '/tmp/forecast.csv')
