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

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.amazon_forecast_integration.controllers \
    import amazon_forecast_integration


@tagged('-at_install', 'post_install')
class TestAmazonForecastController(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env['ir.config_parameter'].sudo()
        cls.config.set_param(
            'amazon_forecast_integration.amazon_forecast', '1')
        cls.config.set_param(
            'amazon_forecast_integration.amazon_access_key', 'access-key')
        cls.config.set_param(
            'amazon_forecast_integration.amazon_secret_access_key',
            'secret-key')
        cls.config.set_param(
            'amazon_forecast_integration.amazon_region', 'ap-south-1')

    def test_get_query_result_returns_forecast_predictions(self):
        forecast_record = SimpleNamespace(
            forecast_arn='arn:aws:forecast:forecast/1',
            item_id='product-a',
        )
        fake_request = SimpleNamespace(
            env=self.env,
            search=MagicMock(return_value=forecast_record),
        )
        forecast_client = MagicMock()
        forecast_client.query_forecast.return_value = {
            'Forecast': {
                'Predictions': {
                    'mean': [{'Timestamp': '2026-01-01', 'Value': 3.0}],
                },
            },
        }
        session = MagicMock()
        session.client.return_value = forecast_client
        controller = amazon_forecast_integration.GraphView()

        with patch.object(
            amazon_forecast_integration,
            'request',
            fake_request,
        ), patch.object(
            amazon_forecast_integration.boto3,
            'Session',
            return_value=session,
        ):
            result = controller.get_query_result()

        session.client.assert_called_once_with('forecastquery')
        forecast_client.query_forecast.assert_called_once_with(
            ForecastArn='arn:aws:forecast:forecast/1',
            Filters={'item_id': 'product-a'},
        )
        self.assertEqual(result, {
            'mean': [{'Timestamp': '2026-01-01', 'Value': 3.0}],
        })
