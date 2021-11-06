# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Author: Nilmar Shereef (<shereef@cybrosys.in>)
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
import logging
_logger = logging.getLogger(__name__)
try:
    import mechanize
    from linkedin import linkedin
    from mechanize_op import MechanizeRedirectHandler

except ImportError:
    _logger.error('Odoo module hr_linkedin_recruitment depends on the several external python package'
                  'Please read the doc/requirement.txt file inside the module.')

import requests
import json
import urlparse
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning


class HrJobShare(models.Model):
    _inherit = 'hr.job'

    update_key = fields.Char(string='Update Key', readonly=True)

    @api.multi
    def share_linkedin(self):
        """ Button function for sharing post """
        credential_dict = self.get_authorize()
        access_token = credential_dict['access_token']
        li_credential = credential_dict['li_credential']

        share_data = {
            "visibility": {"code": "anyone"},
            "comment": self.description
            }

        # URLS
        has_access_url = 'https://api.linkedin.com/v1/companies/%s/relation-to-viewer/is-company-share-enabled?format=json'%(li_credential['page_id'])
        page_share_url = 'https://api.linkedin.com/v1/companies/%s/shares?format=json'%(li_credential['page_id'])

        access_response = self.has_acces_request('GET', has_access_url, access_token)
        access_response_text = access_response.json()
        if access_response_text:
            response = self.share_request('POST', page_share_url, access_token, data=json.dumps(share_data))
            share_response_text = response.json()
            share_response_code = response.status_code
            if share_response_code == 201:
                self.update_key = share_response_text['updateKey']
        else:
            raise Warning("You have no share access in company page.!")

    def has_acces_request(self, method, has_access_url, access_token):
        """ Function will return TRUE if credentials user has the access to update """
        headers = {'x-li-format': 'json', 'Content-Type': 'application/json'}
        params = {}
        params.update({'oauth2_access_token': access_token})
        kw = dict(params=params, headers=headers, timeout=60)
        req_response = requests.request(method.upper(), has_access_url, **kw)
        return req_response

    def share_request(self, method, page_share_url, access_token, data):
        """ Function will return UPDATED KEY , [201] if sharing is OK """
        headers = {'x-li-format': 'json', 'Content-Type': 'application/json'}
        params = {}
        params.update({'oauth2_access_token': access_token})
        kw = dict(data=data, params=params, headers=headers, timeout=60)
        req_response = requests.request(method.upper(), page_share_url, **kw)
        return req_response

    def get_authorize(self):
        """ Supporting function for authenticating operations """
        li_credential = {}
        linkedin_auth_provider = self.env.ref('hr_linkedin_recruitment.provider_linkedin')
        if linkedin_auth_provider.client_id and linkedin_auth_provider.client_secret:
            li_credential['api_key'] = linkedin_auth_provider.client_id
            li_credential['secret_key'] = linkedin_auth_provider.client_secret
        else:
            raise ValidationError(_('LinkedIn Access Credentials are empty.!\n'
                                    'Please fill up in Auth Provider form.'))

        if self.env['ir.values'].get_default('hr.recruitment.config.settings', 'company_page_id'):
            li_credential['page_id'] = self.env['ir.values'].get_default('hr.recruitment.config.settings',
                                                                         'company_page_id')
        else:
            raise Warning(_('Please fill up company page ID in LinkedIn Credential settings.'))
        if self.env['ir.values'].get_default('hr.recruitment.config.settings', 'li_username'):
            li_credential['un'] = self.env['ir.values'].get_default('hr.recruitment.config.settings', 'li_username')
        else:
            raise Warning(_('Please fill up username in LinkedIn Credential settings.'))
        if self.env['ir.values'].get_default('hr.recruitment.config.settings', 'li_password'):
            li_credential['pw'] = self.env['ir.values'].get_default('hr.recruitment.config.settings', 'li_password')
        else:
            raise Warning(_('Please fill up password in LinkedIn Credential settings.'))

        # Browser Data Posting And Signing
        br = mechanize.Browser()
        br.set_cookiejar(mechanize.CookieJar())
        br.handler_classes['_redirect'] = MechanizeRedirectHandler
        br.set_handle_redirect(True)
        br.set_handle_robots(False)
        return_uri = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        li_permissions = ['r_basicprofile', 'r_emailaddress', 'w_share', 'rw_company_admin']
        auth = linkedin.LinkedInAuthentication(li_credential['api_key'],
                                               li_credential['secret_key'],
                                               return_uri,
                                               li_permissions)
        br.open(auth.authorization_url)
        br.select_form(nr=0)
        print "li_credential", li_credential
        br.form['session_key'] = li_credential['un']
        br.form['session_password'] = li_credential['pw']
        r = br.submit()
        try:
            auth.authorization_code = urlparse.parse_qs(urlparse.urlsplit(r.geturl()).query)['code']
        except:
            raise Warning("Please cross check your username and password.!")

        li_suit_credent = {}
        li_suit_credent['access_token'] = str(auth.get_access_token().access_token)
        li_suit_credent['li_credential'] = li_credential
        return li_suit_credent
