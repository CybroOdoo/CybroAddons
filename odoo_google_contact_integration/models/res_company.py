# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

TIMEOUT = 20


class ResCompany(models.Model):
    """Inherit res_company for integrating contacts with Google"""
    _inherit = "res.company"

    contact_client_id = fields.Char(
        string="Client Id", help='People API Client ID')
    contact_client_secret = fields.Char(
        string="Client Secret", help='People API Client Secret')
    contact_redirect_uri = fields.Char(
        string="Authorized redirect URIs",
        compute="_compute_contact_redirect_uri",
        help='People API Authorized redirect URIs')
    contact_company_access_token = fields.Char(
        string="Access Token", copy=False, readonly=True,
        help='People API Access Token')
    contact_company_access_token_expiry = fields.Datetime(
        string="Token expiry", help='People API Token Expiry',
        readonly=True)
    contact_company_refresh_token = fields.Char(
        string="Refresh Token", copy=False, readonly=True,
        help='People API Refresh Token')
    contact_company_authorization_code = fields.Char(
        string="Authorization Code", readonly=True,
        help='People API Authorization Code')

    @api.depends('contact_redirect_uri')
    def _compute_contact_redirect_uri(self):
        """Compute the redirect URI for onedrive and Google Drive"""
        for rec in self:
            base_url = request.env['ir.config_parameter'].get_param(
                'web.base.url')
            rec.contact_redirect_uri = base_url + '/google_contact_authentication'

    def action_google_contact_authenticate(self):
        """Authenticate the connection to Google."""
        if not self.contact_client_id:
            raise ValidationError("Please Enter Client ID")
        if not self.contact_redirect_uri:
            raise ValidationError("Please Enter Client Secret")
        people_scope = 'https://www.googleapis.com/auth/contacts'
        url = (
            "https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
            "&access_type=offline&client_id={}&redirect_uri={}&scope={} "
        ).format(self.contact_client_id,
                 self.contact_redirect_uri, people_scope)
        return {
            "type": 'ir.actions.act_url',
            "url": url,
            "target": "new"
        }

    def action_google_contact_refresh_token(self):
        """Request a refresh token from Google."""
        if not self.contact_client_id:
            raise UserError(
                _('Client ID is not yet configured.'))
        if not self.contact_client_secret:
            raise UserError(
                _('Client Secret is not yet configured.'))
        if not self.contact_company_refresh_token:
            raise UserError(
                _('Refresh Token is not yet configured.'))
        data = {
            'client_id': self.contact_client_id,
            'client_secret': self.contact_client_secret,
            'refresh_token': self.contact_company_refresh_token,
            'grant_type': 'refresh_token',
        }
        response = requests.post(
            'https://accounts.google.com/o/oauth2/token', data=data,
            headers={
                'content-type': 'application/x-www-form-urlencoded'},
            timeout=TIMEOUT)
        if response.json() and response.json().get('access_token'):
            self.write({
                'contact_company_access_token':
                    response.json().get('access_token'),
            })
        else:
            raise UserError(
                _('Something went wrong during the token generation.'
                  ' Please request again an authorization code.')
            )

    def action_import_google_contacts(self):
        """IMPORT Contacts FROM Google TO ODOO"""
        url = ("https://people.googleapis.com/v1/people/me/"
               "connections?personFields=names,addresses,"
               "emailAddresses,phoneNumbers&pageSize=1000")
        headers = {
            'Authorization': f'Bearer {self.contact_company_access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get('connections', [])
            partners = []
            for connection in data:
                cnt_rsr_name = connection.get('resourceName', '')
                etag = connection.get('etag', '')
                names = connection.get('names', [{}])[0]
                first_name = names.get('givenName', '')
                last_name = names.get('familyName', '')
                name = names.get('displayName', '')
                emailAddresses = connection.get('emailAddresses', [{}])[0]
                email = emailAddresses.get('value', '')
                phoneNumbers = connection.get('phoneNumbers', [{}])[0]
                phone = phoneNumbers.get('value', '')
                addresses = connection.get('addresses', [{}])[0]
                street = addresses.get('streetAddress', '')
                street2 = addresses.get('extendedAddress', '')
                city = addresses.get('city', '')
                pin = addresses.get('postalCode', '')
                state = addresses.get('region', '')
                state = self.env['res.country.state'].search(
                    [("name", 'ilike', state)], limit=1)
                state_id = state.id if state else False
                country_code = addresses.get('countryCode', '')
                country = self.env['res.country'].search(
                    [('code', 'ilike', country_code)], limit=1)
                country_id = country.id if country else False
                partner_vals = {
                    'name': name or '',
                    'first_name': first_name or '',
                    'last_name': last_name or '',
                    'email': email or '',
                    'street': street or '',
                    'street2': street2 or '',
                    'city': city or '',
                    'zip': pin or '',
                    'state_id': state_id or False,
                    'country_id': country_id or False,
                    'phone': phone,
                    'google_resource': cnt_rsr_name,
                    'google_etag': etag,
                }
                existing_partner = self.env['res.partner'].search(
                    [('google_resource', '=', cnt_rsr_name)], limit=1)
                if existing_partner:
                    existing_partner.write(partner_vals)
                else:
                    partners.append(partner_vals)
            if partners:
                self.env['res.partner'].create(partners)
            _logger.info("Contact imported successfully!")
        else:
            error_message = f"Failed to import contact. Error: {response.text}"
            raise ValidationError(error_message)
