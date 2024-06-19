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
import requests
from odoo import fields, models, _
from odoo.exceptions import UserError


class InstaPost(models.Model):
    """in the class InstaPost getting the posts of corresponding selected
        instagram account"""
    _name = 'insta.post'

    name = fields.Char(string="Media ID", help="The field defines Media ID")
    caption = fields.Char(string="Caption",
                          help="This field defines the caption")
    post_image = fields.Binary(string='Post Image', attachment=True,
                               help="The field is defined for attaching the"
                                    "post image")
    profile_id = fields.Many2one('insta.profile', string="Profile ID",
                                 help="The field defines the insta profile id")

    def action_update_post(self, access_token):
        """ Action for updating the posts """
        url = ('https://graph.facebook.com/v15.0/%s?fields=id,caption,' +
               'comments_count,is_comment_enabled,like_count,' +
               'media_product_type,media_type,media_url,owner,permalink,' +
               'thumbnail_url,timestamp,username&access_token=%s') % (
                  self.name, access_token)
        media_content = requests.get(url, timeout=5).json()
        if not media_content.get('error'):
            if media_content.get('caption'):
                self.write({
                    'caption': media_content['caption'],
                })
        else:
            raise UserError(_('%s', media_content['error']['message']))
