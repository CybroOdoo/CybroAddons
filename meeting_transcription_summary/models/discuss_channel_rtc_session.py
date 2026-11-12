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

from odoo import api, fields, models


class DiscussChannelRtcSession(models.Model):
    _inherit = 'discuss.channel.rtc.session'

    meeting_subtitles_on = fields.Boolean(
        string='Watching Subtitles',
        help='This participant turned on Subtitle(CC): everyone in the call is captioned meanwhile.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        rtc_sessions = super().create(vals_list)
        # super() opened the call history of calls that just started: give each one a single meeting
        Summary = self.env['discuss.meeting.summary'].sudo()
        for channel in rtc_sessions.channel_id:
            meeting = Summary._get_live_meeting(channel, create=True)
            partners = rtc_sessions.filtered(lambda s: s.channel_id == channel).partner_id
            if meeting and partners:
                meeting.attendee_ids = [(4, partner.id) for partner in partners]
        return rtc_sessions

    def unlink(self):
        # the calls that end with this unlink: their meeting is finalized once super() closed them
        ended_channels = self.channel_id.filtered(lambda c: not (c.rtc_session_ids - self))
        ending_calls = self.env['discuss.call.history'].sudo().search([
            ('channel_id', 'in', ended_channels.ids),
            ('end_dt', '=', False),
        ])
        meetings = self.env['discuss.meeting.summary'].sudo().search([
            ('call_history_id', 'in', ending_calls.ids),
        ])
        # calls that go on without a subtitle viewer who left: their captioning may stop
        viewer_left_channels = self.filtered('meeting_subtitles_on').channel_id - ended_channels
        res = super().unlink()
        meetings._finalize_live_meeting()
        for channel in viewer_left_channels:
            channel._broadcast_meeting_ai_state()
        return res
