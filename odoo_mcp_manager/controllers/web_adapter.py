# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
from .base_adapter import BasePlatformAdapter


class WebAdapter(BasePlatformAdapter):
    """
    Handles requests from the embedded JavaScript web-chat widget.
    Expects a simple JSON body:
        {
            "session_id": "browser-session-or-user-uuid",
            "message":    "user text",
            "attachments": [],        # optional
            "metadata": {}            # optional passthrough
        }
    """

    def normalize(self, raw: dict) -> dict:
        """
        Convert a raw web-chat JSON payload into the normalised bot message dict.

        Expected keys in *raw*:
            session_id  -- unique browser/user identifier (used as platform_user_id)
            message     -- the user's plain-text message
            attachments -- optional list of file attachments
            metadata    -- optional passthrough data returned in the response

        Returns:
            dict with keys: platform, platform_user_id, text, attachments, metadata.
        """
        return {
            'platform':         'web',
            'platform_user_id': raw.get('session_id') or 'anonymous',
            'text':             raw.get('message', ''),
            'attachments':      raw.get('attachments', []),
            'metadata':         raw.get('metadata', {}),
        }

    def format_response(self, response: dict) -> dict:
        """
        Format the internal bot response dict into the JSON structure returned
        to the web-chat client.

        Returns:
            dict with keys:
                reply      -- AI-generated response text
                tool_used  -- name of the Odoo tool that was called (or None)
                session_id -- echo of the originating session identifier
        """
        return {
            'reply':     response.get('text', ''),
            'tool_used': response.get('metadata', {}).get('tool'),
            'session_id': response.get('metadata', {}).get('platform_user_id', ''),
        }
