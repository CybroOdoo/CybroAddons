# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
import base64
import requests
from odoo import fields, models, _
from odoo.exceptions import UserError


class InstaProfile(models.Model):
    """class for adding instagram account"""
    _name = 'insta.profile'

    name = fields.Char(string="Name", readonly=True,
                       help="The name for the insta profile.")
    access_token = fields.Char(string="Access Token",
                               help="The Access Token for the insta profile.")
    username = fields.Char(string='Username', readonly=True,
                           help="The field defines the user name")
    account_id = fields.Char(string='Account ID', readonly=True,
                             help="The field defines the Account id for the"
                                  " insta profile")
    profile_image_url = fields.Binary(attachment=True, string="Profile Image",
                                      help="The profile image can upload here.")

    def action_fetch(self):
        """the action is to check the accounts with the given access token"""
        url = ('https://graph.facebook.com/v15.0/me/accounts?access_token=%s'
               % self.access_token)
        page = requests.get(url)
        page_content = page.json()
        if not page_content.get('error'):
            if page_content['data'][0]['id']:
                url = 'https://graph.facebook.com/v14.0/%s?fields=instagram_business_account&access_token=%s' % (
                    page_content['data'][0]['id'], self.access_token)
                business_account = requests.get(url)
                instagram_business_account = \
                    business_account.json()['instagram_business_account']['id']
                url = ('https://graph.facebook.com/v15.0/%s?fields=name,username,biography,website,followers_count,follows_count,media_count,profile_picture_url&access_token=%s'
                       % (instagram_business_account, self.access_token))
                val = requests.get(url)
                content = val.json()
                if content.get('name'):
                    self.name = content['name']
                if content.get('username'):
                    self.username = content['username']
                if content.get('id'):
                    self.account_id = content['id']
                if content.get('profile_picture_url'):
                    img = base64.b64encode(
                        requests.get(content['profile_picture_url']).content)
                    self.profile_image_url = img
        else:
            raise UserError(_('%s', page_content['error']['message']))

    def action_get_post(self):
        """For getting and write posts to insta post model"""
        url = 'https://graph.facebook.com/v15.0/%s/media?access_token=%s' % (
            self.account_id, self.access_token)
        content = requests.get(url, timeout=5).json()
        if not content.get('error'):
            post_list = [post.name for post in
                         self.env['insta.post'].search([])]
            if content.get('data'):
                for vals in content['data']:
                    if vals['id'] not in post_list:
                        url = 'https://graph.facebook.com/v14.0/%s?fields=id,caption,comments_count,is_comment_enabled,like_count,media_product_type,media_type,media_url,owner,permalink,thumbnail_url,timestamp,username&access_token=%s' % (
                            vals['id'], self.access_token)
                        media_content = requests.get(url, timeout=5).json()
                        if media_content.get('media_type'):
                            if media_content['media_type'] == 'IMAGE':
                                res = self.env['insta.post'].create({
                                    'name': media_content['id'],
                                    'profile_id': self.id,
                                })
                                image_data = base64.b64encode(requests.get(
                                    media_content['media_url']).content)
                                res.write({
                                    'post_image': image_data,
                                })
                                if media_content.get('caption'):
                                    res.write({
                                        'caption': media_content['caption'],
                                    })
                    else:
                        record = self.env['insta.post'].search(
                            [('name', '=', vals['id'])])
                        record.action_update_post(self.access_token)
        else:
            raise UserError(_('%s', content['error']['message']))
