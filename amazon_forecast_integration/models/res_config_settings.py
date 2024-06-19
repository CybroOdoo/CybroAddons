# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shafna K(odoo@cybrosys.com)
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
import boto3
from botocore.exceptions import ClientError
from odoo import fields, models, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    """Class inheriting the res config settings for adding fields for the
    authentication of AWS with Odoo"""
    _inherit = 'res.config.settings'

    amazon_forecast = fields.Boolean(
        string="Amazon Forecast", required=True,
        config_parameter='amazon_forecast_integration.amazon_forecast',
        help="Enable to use Amazon Forecast services.")
    amazon_access_key = fields.Char(
        string="Access Key", help="Provide the access key.", required=True,
        config_parameter='amazon_forecast_integration.amazon_access_key')
    amazon_secret_access_key = fields.Char(
        string="Secret Access Key", required=True,
        config_parameter='amazon_forecast_integration.amazon_secret_access_key',
        help="Provide the secret access key.")
    amazon_region = fields.Char(
        string="Access Key", help="Provide the region.", required=True,
        config_parameter='amazon_forecast_integration.amazon_amazon_region')

    def authenticate_amazon_forecast(self):
        """Function to authenticate the AWS connection with Odoo"""
        try:
            session = boto3.Session(
                aws_access_key_id=self.amazon_access_key,
                aws_secret_access_key=self.amazon_secret_access_key,
                region_name=self.amazon_region
            )
            iam_client = session.client('iam')
            response = iam_client.list_users()
            return response
        except ClientError:
            error_message = _('Invalid Amazon Forecast credentials. Please'
                              ' verify your access key and secret key.')
            raise UserError(error_message)

    def set_values(self):
        """To set the values in the corresponding fields"""
        super().set_values()
        if self.amazon_forecast:
            self.authenticate_amazon_forecast()
            self.env['ir.config_parameter'].set_param(
                'amazon_forecast_integration.amazon_forecast_access_key',
                self.amazon_access_key or '')
            self.env['ir.config_parameter'].set_param(
                'amazon_forecast_integration.amazon_forecast_secret_key',
                self.amazon_secret_access_key or '')
            self.env['ir.config_parameter'].set_param(
                'amazon_forecast_integration.amazon_region',
                self.amazon_region or '')
