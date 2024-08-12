# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
import logging
from werkzeug import urls

_logger = logging.getLogger(__name__)
try:
    import mechanize
    from linkedin_v2 import linkedin
    from urllib.request import HTTPRedirectHandler as MechanizeRedirectHandler
except ImportError:
    _logger.error('Odoo module hr_linkedin_recruitment depends on the several '
                  'external python package Please read the doc/requirement.txt '
                  'file inside the module.')
import json
import requests
from odoo.exceptions import ValidationError
from odoo import http, _
from odoo.http import request
from urllib.parse import urlparse
from urllib.parse import parse_qs


class LinkedinSocial(http.Controller):

    @http.route('/linkedin/redirect', type='http', website=True, auth='public')
    def social_linkedin_callbacks(self):
        """shares post on linkedin"""
        url = request.httprequest.url
        parsed_url = urlparse(url)
        code = parse_qs(parsed_url.query)['code'][0]
        state = parse_qs(parsed_url.query)['state'][0]

        linkedin_auth_provider = request.env.ref(
            'hr_linkedin_recruitment.provider_linkedin')
        linked_in_url = request.env['hr.job'].browse(int(state))

        recruitment = request.env['hr.job']

        access_token = requests.post(
            'https://www.linkedin.com/oauth/v2/accessToken',
            params={
                'Content-Type': 'x-www-form-urlencoded',
                'grant_type': 'authorization_code',
                # This is code obtained on previous step by Python script.
                'code': code,
                # Client ID of your created application
                'client_id': linkedin_auth_provider.client_id,
                # # Client Secret of your created application
                'client_secret': linkedin_auth_provider.client_secret,
                # This should be same as 'redirect_uri' field value of previous Python script.
                'redirect_uri': linked_in_url._get_linkedin_post_redirect_uri(),
            },
        ).json()['access_token']
        li_credential = {}
        linkedin_auth_provider = request.env.ref(
            'hr_linkedin_recruitment.provider_linkedin')
        if (linkedin_auth_provider.client_id and
                linkedin_auth_provider.client_secret):
            li_credential['api_key'] = linkedin_auth_provider.client_id
            li_credential['secret_key'] = linkedin_auth_provider.client_secret
        else:
            raise ValidationError(_('LinkedIn Access Credentials are empty.!\n'
                                    'Please fill up in Auth Provider form.'))

        if request.env['ir.config_parameter'].sudo().get_param(
                'recruitment.li_username'):
            li_credential['un'] = request.env[
                'ir.config_parameter'].sudo().get_param(
                'recruitment.li_username')
        else:
            raise ValidationError(
                _('Please fill up username in LinkedIn Credential settings.'))

        if request.env['ir.config_parameter'].sudo().get_param(
                'recruitment.li_password'):
            li_credential['pw'] = request.env[
                'ir.config_parameter'].sudo().get_param(
                'recruitment.li_password')
        else:
            raise ValidationError(
                _('Please fill up password in LinkedIn Credential settings.'))

        url = 'https://api.linkedin.com/v2/ugcPosts'

        li_suit_credent = {}
        li_suit_credent['access_token'] = access_token
        member_url = 'https://api.linkedin.com/v2/userinfo'
        response = recruitment.get_urn('GET', member_url,
                                       li_suit_credent['access_token'])
        urn_response_text = response.json()
        li_credential['profile_urn'] = urn_response_text['sub']
        li_suit_credent['li_credential'] = li_credential
        payload = json.dumps({
            "author": "urn:li:person:" + li_credential['profile_urn'],
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": linked_in_url.name
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        })
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'X-Restli-Protocol-Version': '2.0.0',
            'Content-Type': 'application/json',
        }
        if linked_in_url.name:
            response = requests.request("POST", url, data=payload,
                                        headers=headers)
            share_response_text = response.json()
            linked_in_url.write({
                'access_token': access_token + '+' + share_response_text['id']
            })

            share_response_code = response.status_code

            if share_response_code == 201:
                linked_in_url.update_key = True
            elif share_response_code == 404:
                raise Warning("Resource does not exist.!")
            elif share_response_code == 409:
                raise Warning("Already shared!")
            else:
                raise Warning("Error!! Check your connection...")
        else:
            raise Warning("Provide a Job description....")

        return_uri = 'https://www.linkedin.com/oauth/v2/authorization'
        li_permissions = [' w_organization_social_feed ', ' r_liteprofile ',
                          ' r_organization_social_feed ', ' r_ads ',
                          'w_member_social_feed', 'r_member_social',
                          'r_compliance', 'w_compliance']

        auth = linkedin.LinkedInAuthentication(li_credential['api_key'],
                                               li_credential['secret_key'],
                                               return_uri,
                                               li_permissions)
        li_suit_credent = {}
        li_suit_credent['access_token'] = access_token
        li_credential['profile_urn'] = share_response_text['id']
        li_suit_credent['li_credential'] = li_credential

        url = urls.url_join(
            http.request.env['ir.config_parameter'].sudo().get_param(
                'web.base.url'),
            'web#id=%(id)s&model=hr.job&action=%(action)s&view_type=form' % {
                'id': state,
                'action': request.env.ref('hr_recruitment.action_hr_job').id
            })
        return request.redirect(url)
