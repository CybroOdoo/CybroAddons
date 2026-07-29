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
from odoo import http
from odoo.http import request
import boto3


class GraphView(http.Controller):
    """The ProjectFilter class provides the filter option to the js.
    When applying the filter returns the corresponding data."""

    @http.route('/get_query_result', auth='public', type='json')
    def get_query_result(self):
        """Function to return values into js"""
        values = request.env['amazon.dataset'].forecast_values()
        amazon_forecast = values['amazon_forecast']
        if amazon_forecast:
            amazon_access_key = values['amazon_access_key']
            amazon_secret_access_key = values['amazon_secret_access_key']
            amazon_region = values['amazon_region']
            session = boto3.Session(
                aws_access_key_id=amazon_access_key,
                aws_secret_access_key=amazon_secret_access_key,
                region_name=amazon_region
            )
            forecast_client = session.client('forecastquery')
            data = request.search([], limit=1)
            response = forecast_client.query_forecast(
                ForecastArn=data.forecast_arn,
                Filters={
                    'item_id': data.item_id
                }
            )
            forecast_result = response['Forecast']['Predictions']
            return forecast_result