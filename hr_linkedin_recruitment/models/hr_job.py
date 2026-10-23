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
from urllib.parse import urlencode, urljoin
import requests
from odoo import fields, models
from odoo.exceptions import ValidationError


class HrJobShare(models.Model):
    """Recruitment of different job positions."""
    _inherit = 'hr.job'

    update_key = fields.Char(string='Update Key', readonly=True)
    access_token = fields.Char(string='Access Token',
                               help='Access token for your linkedin app')
    is_comments = fields.Boolean(default=False, string='Likes Comments',
                              help='Used to display the like and comment retrieving button')
    is_like_comment = fields.Boolean(default=False, string='Likes comment',
                                  help='Used to display the smart buttons of likes and comments')
    post_likes = fields.Integer(string='Likes Count',
                                help="Total Number of likes in the shared post")
    post_commands = fields.Integer(string='Comments Count',
                                   help="Total Number of Comments in the shared post")
    comments_ids = fields.One2many('linkedin.comments', 'post_id',
                                   string='LinkedIn Comments')

    def _get_linkedin_post_redirect_uri(self):
        """Find redirecting URL."""
        return urljoin(self.get_base_url(), '/linkedin/redirect')

    def share_linkedin(self):
        """Button function for sharing post."""
        self.is_comments = True
        linkedin_auth_provider = self.env.ref(
            'hr_linkedin_recruitment.provider_linkedin')
        if linkedin_auth_provider.client_id and linkedin_auth_provider.client_secret:
            linkedin_client_id = linkedin_auth_provider.client_id
            params = {
                'response_type': 'code',
                'client_id': linkedin_client_id,
                'redirect_uri': self._get_linkedin_post_redirect_uri(),
                'state': self.id,
                'scope': 'w_member_social r_1st_connections_size r_ads '
                         'r_ads_reporting r_basicprofile r_organization_admin '
                         'r_organization_social rw_ads rw_organization_admin '
                         'w_member_social w_organization_social openid profile email'
            }
        else:
            raise ValidationError('LinkedIn Access Credentials are empty.\n'
                                    'Please fill up in Auth Provider form.')
        return {
            'type': 'ir.actions.act_url',
            'url': f'https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}',
            'target': 'self'
        }

    def share_request(self, method, page_share_url, access_token, data):
        """Return updated key and response from LinkedIn."""
        headers = {'x-li-format': 'json', 'Content-Type': 'application/json'}
        params = {}
        params.update({'oauth2_access_token': access_token})
        kw = dict(data=data, params=params, headers=headers, timeout=60)
        req_response = requests.request(method.upper(), page_share_url, **kw)
        return req_response

    def get_urn(self, method, has_access_url, access_token):
        """Return response for member URN request."""
        headers = {'x-li-format': 'json', 'Content-Type': 'application/json'}
        params = {}
        params.update({'oauth2_access_token': access_token})
        kw = dict(params=params, headers=headers, timeout=60)
        req_response = requests.request(method.upper(), has_access_url, **kw)
        return req_response

    def user_response_like(self):
        """Refresh and retrieve latest likes and comments count from LinkedIn."""
        if self.access_token:
            self.likes_comments()
        return None

    def likes_comments(self):
        """Retrieve total count of likes and comments."""
        self.is_like_comment = True
        urn = self.access_token.split('+')[1]
        url = "https://api.linkedin.com/v2/socialActions/" + urn
        payload = {}
        headers = {
            'Authorization': 'Bearer ' + self.access_token.split('+')[0],
            'LinkedIn-Version': '202308',
        }
        response = requests.request("GET", url, headers=headers)
        response_comm_like = response.json()
        self.post_likes = response_comm_like['likesSummary']['totalLikes']
        self.post_commands = response_comm_like["commentsSummary"][
            'aggregatedTotalComments']
        comment_url = "https://api.linkedin.com/v2/socialActions/" + urn + "/comments"
        headers = {
            'LinkedIn-Version': '202308',
            'Authorization': 'Bearer ' + self.access_token.split('+')[0],
        }
        response = requests.request("GET", comment_url, headers=headers,
                                    data=payload)
        response_commets = response.json()

        existing_comment_ids = self.env['linkedin.comments'].search([
            ('post_id', '=', self.id)
        ]).mapped('comments_id')
        for record in response_commets.get("elements", []):
            if record['id'] not in existing_comment_ids:
                self.env['linkedin.comments'].create({
                    'post_id': self.id,
                    'comments_id': record['id'],
                    'linkedin_comments': record['message']['text'],
                })

    def user_response_commends(self):
        """Return the comments of the shared post."""
        action = self.env['ir.actions.act_window']._for_xml_id(
            'hr_linkedin_recruitment.hr_recruitment_comments'
        )
        action['domain'] = [('post_id', '=', self.id)]
        return action

    def view_shared_post(self):
        """Direct link for viewing the shared post page in linkedin"""
        url = "https://api.linkedin.com/v2/me"
        payload = ""
        headers = {
            'LinkedIn-Version': '202208',
            'Authorization': 'Bearer ' + self.access_token.split('+')[0],
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        response_activity = response.json()
        activity_urn = response_activity["vanityName"]
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://www.linkedin.com/in/%s' % activity_urn + '/recent-activity/',
            'target': 'self'
        }
