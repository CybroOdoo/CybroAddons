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

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('-at_install', 'post_install')
class TestAmazonForecastSettings(TransactionCase):
    def _settings(self):
        return self.env['res.config.settings'].create({
            'amazon_forecast': True,
            'amazon_access_key': 'access-key',
            'amazon_secret_access_key': 'secret-key',
            'amazon_region': 'ap-south-1',
        })

    def test_authenticate_amazon_forecast_returns_iam_users_response(self):
        settings = self._settings()
        iam_client = MagicMock()
        iam_client.list_users.return_value = {'Users': []}
        session = MagicMock()
        session.client.return_value = iam_client

        with patch(
            'odoo.addons.amazon_forecast_integration.models.'
            'res_config_settings.boto3.Session',
            return_value=session,
        ):
            response = settings.authenticate_amazon_forecast()

        session.client.assert_called_once_with('iam')
        self.assertEqual(response, {'Users': []})

    def test_authenticate_amazon_forecast_raises_user_error_on_client_error(self):
        settings = self._settings()
        iam_client = MagicMock()
        iam_client.list_users.side_effect = ClientError(
            {'Error': {'Code': 'InvalidClientTokenId',
                       'Message': 'Invalid credentials'}},
            'ListUsers',
        )
        session = MagicMock()
        session.client.return_value = iam_client

        with patch(
            'odoo.addons.amazon_forecast_integration.models.'
            'res_config_settings.boto3.Session',
            return_value=session,
        ), self.assertRaises(UserError):
            settings.authenticate_amazon_forecast()

    def test_set_values_authenticates_and_persists_amazon_parameters(self):
        settings = self._settings()
        config = self.env['ir.config_parameter'].sudo()

        with patch.object(
            type(settings),
            'authenticate_amazon_forecast',
            return_value={'Users': []},
        ) as authenticate, patch(
            'odoo.addons.stock.models.res_config_settings.'
            'ResConfigSettings.set_values',
            return_value=None,
        ):
            settings.set_values()

        authenticate.assert_called_once()
        self.assertEqual(
            config.get_param(
                'amazon_forecast_integration.amazon_forecast_access_key'),
            'access-key',
        )
        self.assertEqual(
            config.get_param(
                'amazon_forecast_integration.amazon_forecast_secret_key'),
            'secret-key',
        )
        self.assertEqual(
            config.get_param('amazon_forecast_integration.amazon_region'),
            'ap-south-1',
        )
