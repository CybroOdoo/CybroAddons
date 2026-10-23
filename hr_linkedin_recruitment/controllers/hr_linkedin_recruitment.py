# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import json
from urllib.parse import parse_qs, urlparse
import requests
from odoo import http
from odoo.exceptions import UserError, ValidationError
from odoo.http import request


class LinkedinSocial(http.Controller):
    """Controller handling LinkedIn OAuth callback and posting job updates to LinkedIn."""

    @http.route('/linkedin/redirect', type='http', auth='user')
    def social_linkedin_callbacks(self):
        """Share post on LinkedIn."""
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
                'code': code,
                'client_id': linkedin_auth_provider.client_id,
                'client_secret': linkedin_auth_provider.client_secret,
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
            raise ValidationError('LinkedIn Access Credentials are empty.\n'
                                  'Please fill up in Auth Provider form.')
        if request.env['ir.config_parameter'].sudo().get_str(
                'recruitment.li_username'):
            li_credential['un'] = request.env[
                'ir.config_parameter'].sudo().get_str(
                'recruitment.li_username')
        else:
            raise ValidationError('Please fill up username in LinkedIn Credential settings.')
        if request.env['ir.config_parameter'].sudo().get_str(
                'recruitment.li_password'):
            li_credential['pw'] = request.env[
                'ir.config_parameter'].sudo().get_str(
                'recruitment.li_password')
        else:
            raise ValidationError('Please fill up password in LinkedIn Credential settings.')
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
                raise UserError("Resource does not exist.")
            elif share_response_code == 409:
                raise UserError("Already shared.")
            else:
                raise UserError("Error! Check your connection.")
        else:
            raise UserError("Provide a job description.")
        li_suit_credent = {}
        li_suit_credent['access_token'] = access_token
        li_credential['profile_urn'] = share_response_text['id']
        li_suit_credent['li_credential'] = li_credential
        return request.redirect(f'/odoo/hr.job/{state}')
