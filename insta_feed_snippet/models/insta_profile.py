# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Henna Mehjabin(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (LGPL-3 v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (LGPL-3 v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (LGPL-3 v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import requests
from odoo import _, fields, models
from odoo.exceptions import UserError


class InstaProfile(models.Model):
    """Instagram Profiles"""
    _name = 'insta.profile'
    _description = 'Instagram Profile'

    name = fields.Char(string="Name", readonly=True)
    access_token = fields.Char("Access Token")
    username = fields.Char('Username', readonly=True)
    account_id = fields.Char('Account ID', readonly=True)
    profile_image_url = fields.Binary(attachment=True)

    def action_fetch(self):
        """Fetch Instagram account"""
        url = "https://graph.facebook.com/v15.0/me/accounts"
        params = {'access_token': self.access_token}
        page = requests.get(url, params=params, timeout=10)
        try:
            page_content = page.json()
        except ValueError as e:
            raise UserError(_("JSON Decode Error: %s") % e) from e
        if page_content.get('error'):
            raise UserError(page_content['error'].get('message'))
        if not page_content.get('data'):
            raise UserError(_("No pages returned for this token."))
        page_id = page_content['data'][0].get('id')
        url = f"https://graph.facebook.com/v15.0/{page_id}"
        params = {
            'fields': 'instagram_business_account',
            'access_token': self.access_token
        }
        business_account = requests.get(url, params=params, timeout=10)
        try:
            business_json = business_account.json()
        except ValueError as e:
            raise UserError(_("JSON Decode Error: %s") % e) from e
        if business_json.get('error'):
            raise UserError(business_json['error'].get('message'))
        instagram_business_account = business_json.get(
            'instagram_business_account', {}
        ).get('id')
        if not instagram_business_account:
            raise UserError(
                _("Instagram Business Account not linked to this page.")
            )
        url = f"https://graph.facebook.com/v15.0/{instagram_business_account}"
        params = {
            'fields': (
                'name,username,biography,website,followers_count,'
                'follows_count,media_count,profile_picture_url'
            ),
            'access_token': self.access_token
        }
        val = requests.get(url, params=params, timeout=10)
        try:
            content = val.json()
        except ValueError as e:
            raise UserError(_("JSON Decode Error: %s") % e) from e
        if content.get('error'):
            raise UserError(content['error'].get('message'))
        self.name = content.get('name')
        self.username = content.get('username')
        self.account_id = content.get('id')
        if content.get('profile_picture_url'):
            img_response = requests.get(
                content['profile_picture_url'], timeout=10
            )
            self.profile_image_url = base64.b64encode(
                img_response.content
            )

    def action_get_post(self):
        """Fetch Instagram posts"""
        url = (
            f"https://graph.facebook.com/v15.0/"
            f"{self.account_id}/media"
            f"?access_token={self.access_token}"
        )
        response = requests.get(url, timeout=10)
        try:
            content = response.json()
        except ValueError as e:
            raise UserError(_("JSON Decode Error: %s") % e) from e
        if content.get('error'):
            raise UserError(content['error'].get('message'))
        records = self.env['insta.post'].search([])
        post_list = records.mapped('name')
        if not content.get('data'):
            return
        for vals in content['data']:
            media_id = vals.get('id')
            if media_id in post_list:
                record = self.env['insta.post'].search(
                    [('name', '=', media_id)], limit=1
                )
                record.action_update_post(self.access_token)
                continue
            media_url = (
                f"https://graph.facebook.com/v14.0/{media_id}"
                f"?fields=id,caption,comments_count,is_comment_enabled,"
                f"like_count,media_product_type,media_type,media_url,"
                f"owner,permalink,thumbnail_url,timestamp,username"
                f"&access_token={self.access_token}"
            )
            media_response = requests.get(media_url, timeout=10)
            try:
                media_content = media_response.json()
            except ValueError as e:
                raise UserError(_("JSON Decode Error: %s") % e) from e
            if media_content.get('error'):
                raise UserError(media_content['error'].get('message'))
            if media_content.get('media_type') != 'IMAGE':
                continue
            res = self.env['insta.post'].create({
                'name': media_content.get('id'),
                'profile_id': self.id,
            })
            image_resp = requests.get(
                media_content.get('media_url'),
                timeout=10
            )
            res.write({
                'post_image': base64.b64encode(image_resp.content),
            })
            if media_content.get('caption'):
                res.write({
                    'caption': media_content.get('caption'),
                })
