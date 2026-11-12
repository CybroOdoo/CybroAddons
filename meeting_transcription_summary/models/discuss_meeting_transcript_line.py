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

from odoo import fields, models


class DiscussMeetingTranscriptLine(models.Model):
    """One final caption of a live call, stored server-side as it is transcribed.

    Every participant's browser sends only its own microphone, so each line is recorded once,
    by the speaker's own request; the meeting's transcript is assembled from them when the call ends.
    """
    _name = 'discuss.meeting.transcript.line'
    _description = 'Discuss Meeting Transcript Line'
    _order = 'time, id'

    summary_id = fields.Many2one('discuss.meeting.summary', required=True, index=True, ondelete='cascade')
    channel_member_id = fields.Many2one('discuss.channel.member', string='Speaker Member', ondelete='set null')
    speaker_name = fields.Char(string='Speaker', required=True)
    text = fields.Text(required=True)
    time = fields.Datetime(default=fields.Datetime.now, required=True)
