# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies @cybrosys(odoo@cybrosys.com)
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
import tweepy

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class RecruitmentTwitter(models.Model):
    """Post job position on Twitter"""
    _inherit = 'hr.job'

    image_1920 = fields.Binary(string="Poster", attachment=True,
                               help="Upload image to post")

    def action_job_post(self):
        """This function is to post job position on Twitter"""

        job_post_url = str(self.get_base_url()) + str("/jobs/detail/") + str(
            self.id)
        consumer_key = self.env['ir.config_parameter'].get_param(
            'recruitment_twitter.consumer_key')
        consumer_secret = self.env['ir.config_parameter'].get_param(
            'recruitment_twitter.consumer_secret')
        access_token = self.env['ir.config_parameter'].get_param(
            'recruitment_twitter.access_token')
        access_token_secret = self.env['ir.config_parameter'].get_param(
            'recruitment_twitter.access_token_secret')
        if consumer_key and consumer_secret and access_token and access_token_secret:
            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth)
            try:
                api.verify_credentials()
            except Exception as exc:
                _logger.warning(exc)
                raise UserError(_('Failed Authentication')) from exc
            attachment = self.env["ir.attachment"].search(
                ['|', ('res_field', '!=', False), ('res_field', '=', False),
                 ('res_id', '=', self.id),
                 ('res_model', '=', 'hr.job')], limit=1)

            file_path = attachment._full_path(attachment.store_fname)
            media = api.media_upload(file_path)
            api.update_status(status=job_post_url,
                              media_ids=[media.media_id])
            message = {
                'type': 'success',
                'title': _('Success!'),
                'message': _('Posted successfully.'),
                'sticky': False,
            }
            return {'type': 'ir.actions.client',
                    'tag': 'display_notification', 'params': message}
        raise UserError(_('Please fill API credentials properly.'))
