# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Vishnu KP(odoo@cybrosys.com)
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
################################################################################
import logging
import tweepy
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrJob(models.Model):
    """Post job position on Twitter"""
    _inherit = 'hr.job'

    attachment_ids = fields.Many2many('ir.attachment', 'res_id',
                                      string="Twitter Poster",
                                      help="Upload image to post")

    def action_job_post(self):
        """
        Post the job position on Twitter.

        This method posts the job position on Twitter using the configured API
        credentials and the attached image. The job position URL
        is included in the tweet.

        :return: Dictionary with notification details if posted successfully.
        :raise: UserError if API credentials are missing or invalid, or if no
         poster is attached.
        """
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

        if (consumer_key and consumer_secret and access_token and
                access_token_secret):
            client = tweepy.Client(
                consumer_key=consumer_key, consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret)
            if self.attachment_ids:
                file_path = max(self.attachment_ids)._full_path(
                    max(self.attachment_ids).store_fname)
                try:
                    auth = tweepy.OAuth1UserHandler(consumer_key,
                                                    consumer_secret)
                    auth.set_access_token(access_token, access_token_secret)
                    tweepy_api = tweepy.API(auth)
                    media = tweepy_api.media_upload(file_path)
                    client.create_tweet(text=job_post_url,
                                        media_ids=[media.media_id])
                    message = {
                        'type': 'success',
                        'title': _('Success!'),
                        'message': _('Posted successfully.'),
                        'sticky': False,
                    }
                    return {'type': 'ir.actions.client',
                            'tag': 'display_notification', 'params': message}
                except Exception as exc:
                    _logger.warning(exc)
                    raise UserError(_('Failed Authentication')) from exc
            else:
                raise UserError(_('Please add a poster.'))
        raise UserError(_('Please fill API credentials properly.'))

    @api.onchange('attachment_ids')
    def _onchange_attachment_ids(self):
        """
        Onchange method triggered when the attached images are changed.
        This method checks if the attachments are of type 'image'.
        If any attachment is not an image, it raises a UserError.
        """
        for attachment in self.attachment_ids:
            if attachment.index_content != 'image':
                raise UserError(_('Only images allowed.'))
