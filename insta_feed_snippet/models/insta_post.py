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
import requests
from odoo import fields, models
from odoo.exceptions import UserError


class InstaPost(models.Model):
    """The model is for showing the instagram post"""
    _name = 'insta.post'
    _description = 'Instagram Post'

    name = fields.Char(string="Media ID",
                       help='The Media id of the instagram page')
    caption = fields.Char("Caption", help='Instagram Caption')
    post_image = fields.Binary(string='Post Image', attachment=True,
                               help='Instagram post')
    profile_id = fields.Many2one('insta.profile',string='Profile Id',help='Instagram Profile Id')

    def action_update_post(self, access_token):
        """For fetching the post on instagram"""
        params = {
            "fields": (
                "id,caption,comments_count,is_comment_enabled,"
                "like_count,media_product_type,media_type,media_url,"
                "owner,permalink,thumbnail_url,timestamp,username"
            ),
            "access_token": access_token,
        }
        url = f"https://graph.facebook.com/v15.0/{self.name}"
        media_content = requests.get(url, params=params, timeout=5).json()
        if not media_content.get('error'):
            if media_content.get('caption'):
                self.write({'caption': media_content['caption']})
        else:
            error_msg = media_content.get('error', {}).get('message', 'Unknown error')
            raise UserError(error_msg)
