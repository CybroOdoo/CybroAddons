# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
import base64
import logging
import re
import requests

from odoo import models, _

_logger = logging.getLogger(__name__)


class Slide(models.Model):
    _inherit = 'slide.slide'

    def _fetch_youtube_metadata(self, image_url_only=False):
        """Override to safely handle timeouts when downloading YouTube thumbnails."""
        self.ensure_one()
        google_app_key = self.env['website'].get_current_website().sudo().website_slide_google_app_key
        error_message = False
        try:
            response = requests.get(
                'https://www.googleapis.com/youtube/v3/videos',
                timeout=10,
                params={
                    'fields': 'items(id,snippet,contentDetails)',
                    'id': self.youtube_id,
                    'key': google_app_key,
                    'part': 'snippet,contentDetails'
                }
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            error_message = e.response.content
            if 'application/json' in e.response.headers.get('content-type'):
                json_response = e.response.json()
                if json_response.get('error', {}).get('code') == 404:
                    return {}, _('Your video could not be found on YouTube, please check the link and/or privacy settings')
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            error_message = str(e)
        except requests.exceptions.RequestException as e:
            error_message = str(e)

        if not error_message:
            response = response.json()
            if response.get('error'):
                error_message = response.get('error', {}).get('errors', [{}])[0].get('reason')

            if not response.get('items'):
                error_message = _('Your video could not be found on YouTube, please check the link and/or privacy settings')

        if error_message:
            _logger.warning('Could not fetch YouTube metadata: %s', error_message)
            return {}, error_message

        slide_metadata = {'slide_type': 'youtube_video'}
        youtube_values = response.get('items')[0]
        youtube_duration = youtube_values.get('contentDetails', {}).get('duration')
        if youtube_duration:
            parsed_duration = re.search(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', youtube_duration)
            if parsed_duration:
                slide_metadata['completion_time'] = (int(parsed_duration.group(1) or 0)) + \
                                                    (int(parsed_duration.group(2) or 0) / 60) + \
                                                    (round(int(parsed_duration.group(3) or 0) / 60) / 60)

        if youtube_values.get('snippet'):
            snippet = youtube_values['snippet']
            slide_metadata.update({
                'name': snippet['title'],
                'description': snippet['description'],
            })

            thumbnail_url = snippet.get('thumbnails', {}).get('high', {}).get('url') or \
                            snippet.get('thumbnails', {}).get('medium', {}).get('url') or \
                            snippet.get('thumbnails', {}).get('default', {}).get('url')
            if thumbnail_url:
                if image_url_only:
                    slide_metadata['image_url'] = thumbnail_url
                else:
                    try:
                        res = requests.get(thumbnail_url, timeout=10)
                        res.raise_for_status()
                        slide_metadata['image_1920'] = base64.b64encode(res.content)
                    except Exception as e:
                        _logger.warning('Could not fetch YouTube thumbnail (%s): %s', thumbnail_url, e)

        return slide_metadata, None
