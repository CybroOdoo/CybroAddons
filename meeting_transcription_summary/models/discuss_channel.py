# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import datetime

from odoo import models


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    def _broadcast_meeting_subtitle(self, partner_name, text, partner_id=None, member_id=None):
        """Broadcasts real-time meeting subtitles to all active members of this channel.

        Private (not callable over RPC): only the transcription endpoint may caption, with the
        speaker identity it checked itself.

        ``member_id`` tells speakers apart even when they share a partner (all guests use the
        public partner).
        """
        self.ensure_one()
        payload = {
            'channel_id': self.id,
            'partner_id': partner_id or self.env.user.partner_id.id,
            'partner_name': partner_name or self.env.user.partner_id.name or "Participant",
            'text': text,
            'member_id': member_id,
            'time': datetime.now().strftime("%H:%M:%S"),
        }
        self._bus_send("discuss.channel/meeting_subtitle", payload)
        return True

    def _get_meeting_ai_state(self):
        """What the running call needs from every participant's microphone.

        ``transcribe``: the call is being transcribed into its meeting summary (an internal user
        in the call turns it on for everyone). ``subtitles``: at least one participant watches
        Subtitle(CC), so everyone's speech is captioned.
        """
        self.ensure_one()
        meeting = self.env['discuss.meeting.summary'].sudo()._get_live_meeting(self)
        return {
            'channel_id': self.id,
            'transcribe': bool(meeting.transcribe_enabled),
            'subtitles': any(self.sudo().rtc_session_ids.mapped('meeting_subtitles_on')),
        }

    def _broadcast_meeting_ai_state(self):
        for channel in self:
            channel._bus_send("discuss.channel/meeting_ai_state", channel._get_meeting_ai_state())
