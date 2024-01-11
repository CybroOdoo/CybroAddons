# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
import base64
import requests
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    """Inheriting company model for configuring Zoom Odoo connector"""
    _inherit = "res.company"

    zoom_client = fields.Char(
        string="Client ID", help='Zoom developer console client Id')
    zoom_client_secret = fields.Char(
        string="Client Secret", help='Zoom developer console client secret')
    zoom_redirect_uri = fields.Char(
        string="Authorized Redirect URI",
        compute='_compute_zoom_redirect_url',
        help='This should be added as Redirect URL for OAuth in Zoom')
    zoom_company_access_token = fields.Char(string='Access Token',
                                            copy=False,
                                            help='Access token for '
                                                 'respective company')
    zoom_company_access_token_expiry = fields.Datetime(
        string='Token expiry', help='Access token expiration')
    zoom_company_refresh_token = fields.Char(string='Refresh Token',
                                             copy=False,
                                             help='Refresh token for '
                                                  'respective company')
    zoom_company_authorization_code = fields.Char(string="Authorization Code",
                                                  help='Authorization Code '
                                                       'for respective company')

    def _compute_zoom_redirect_url(self):
        """Method for computing the value of field zoom_redirect_url"""
        for record in self:
            record.zoom_redirect_uri = (self.env[
                                            'ir.config_parameter'].sudo().
                                        get_param(
                'web.base.url') + '/zoom_meet_authentication')

    def action_zoom_meet_company_authenticate(self):
        """Authentication for zoom"""
        if not self.zoom_client:
            raise ValidationError("Please Enter Client ID")
        if not self.zoom_redirect_uri:
            raise ValidationError("Please Enter Client Secret")
        return {
            "type": 'ir.actions.act_url',
            "url": (
                "https://zoom.us/oauth/authorize?response_type=code"
                "&client_id={}&redirect_uri={}"
            ).format(self.zoom_client, self.zoom_redirect_uri),
            "target": "current"
        }

    def action_zoom_meet_company_refresh_token(self):
        """Generate refresh token"""
        if not self.zoom_client:
            raise ValidationError(
                _('Client ID is not yet configured.'))
        if not self.zoom_client_secret:
            raise ValidationError(
                _('Client Secret is not yet configured.'))
        if not self.zoom_company_refresh_token:
            raise ValidationError(
                _('Refresh Token is not yet configured.'))
        data = {
            'refresh_token': self.zoom_company_refresh_token,
            'grant_type': 'refresh_token',
        }
        response = requests.post(
            'https://zoom.us/oauth/token', data=data,
            headers={
                'Authorization': 'Basic ' + base64.b64encode(str(
                    self.zoom_client + ":" + self.zoom_client_secret).encode(
                    'utf-8')).decode('utf-8'),
                'content-type': 'application/x-www-form-urlencoded'},
            timeout=20)
        if response.json() and response.json().get('access_token'):
            self.write({
                'zoom_company_access_token':
                    response.json().get('access_token'),
            })
        else:
            raise ValidationError(
                _('Something went wrong during the token generation.'
                  'Please request for an authorization code again.'))
