# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
#
################################################################################
import base64
import requests
from odoo import fields, models
from odoo.exceptions import UserError


class InstaProfile(models.Model):
    _name = 'insta.profile'
    _description = 'Instagram Profile'

    name = fields.Char(string="Name", readonly=True)
    access_token = fields.Char("Access Token")
    username = fields.Char('Username', readonly=True)
    account_id = fields.Char('Account ID', readonly=True)
    profile_image_url = fields.Binary(attachment=True)

    def action_fetch(self):
        """This function fetches instagram account"""
        url = "https://graph.facebook.com/v15.0/me/accounts"
        params = {'access_token': self.access_token}
        page = requests.get(url, params=params, timeout=10)
        try:
            page_content = page.json()
        except Exception as e:
            raise UserError(f"JSON Decode Error: {e}") from e
        if page_content.get('error'):
            raise UserError(page_content['error'].get('message', 'Unknown error'))
        if not page_content.get('data'):
            raise UserError("No pages returned for this token.")
        page_id = page_content['data'][0].get('id')
        url = f"https://graph.facebook.com/v15.0/{page_id}"
        params = {
            'fields': 'instagram_business_account',
            'access_token': self.access_token
        }
        business_account = requests.get(url, params=params, timeout=10)
        try:
            business_json = business_account.json()
        except Exception as e:
            raise UserError(f"JSON Decode Error: {e}") from e
        if business_json.get('error'):
            raise UserError(business_json['error'].get('message', 'Unknown error'))
        instagram_business_account = business_json.get(
            'instagram_business_account', {}
        ).get('id')
        if not instagram_business_account:
            raise UserError("Instagram Business Account not linked to this page.")
        url = f"https://graph.facebook.com/v15.0/{instagram_business_account}"
        params = {
            'fields': 'name,username,biography,website,followers_count,'
                      'follows_count,media_count,profile_picture_url',
            'access_token': self.access_token
        }
        val = requests.get(url, params=params, timeout=10)
        try:
            content = val.json()
        except Exception as e:
            raise UserError(f"JSON Decode Error: {e}") from e
        if content.get('error'):
            raise UserError(content['error'].get('message', 'Unknown error'))
        self.name = content.get('name')
        self.username = content.get('username')
        self.account_id = content.get('id')
        if content.get('profile_picture_url'):
            img_response = requests.get(content['profile_picture_url'], timeout=10)
            self.profile_image_url = base64.b64encode(img_response.content)

    def action_get_post(self):
        """This function fetches instagram post"""
        url = f"https://graph.facebook.com/v15.0/{self.account_id}/media?access_token={self.access_token}"
        content = requests.get(url, timeout=5).json()
        if content.get('error'):
            raise UserError(content['error'].get('message', 'Unknown error'))
        post_list = []
        records = self.env['insta.post'].search([])
        for post in records:
            post_list.append(post.name)
        if content.get('data'):
            for vals in content['data']:
                if vals['id'] not in post_list:
                    url = (
                        f"https://graph.facebook.com/v14.0/{vals['id']}?fields="
                        "id,caption,comments_count,is_comment_enabled,"
                        "like_count,media_product_type,media_type,"
                        "media_url,owner,permalink,thumbnail_url,"
                        "timestamp,username"
                        f"&access_token={self.access_token}"
                    )
                    media_content = requests.get(url, timeout=5).json()
                    if media_content.get('media_type') == 'IMAGE':
                        res = self.env['insta.post'].create({
                            'name': media_content['id'],
                            'profile_id': self.id,
                        })
                        image_data = base64.b64encode(
                            requests.get(
                                media_content['media_url'],
                                timeout=10
                            ).content
                        )
                        res.write({'post_image': image_data})
                        if media_content.get('caption'):
                            res.write({
                                'caption': media_content['caption'],
                            })
                else:
                    record = self.env['insta.post'].search(
                        [('name', '=', vals['id'])]
                    )
                    record.action_update_post(self.access_token)
                    