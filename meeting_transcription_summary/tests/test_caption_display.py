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
from unittest.mock import patch

from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.meeting_transcription_summary.tools import stt_client


@tagged('post_install', '-at_install')
class TestCaptionDisplay(HttpCase):
    """Captions as shown in a real call: stacked, each kept long enough to be read."""

    def test_caption_lines(self):
        bob = new_test_user(self.env, login='caption_bob', name='Bob', groups='base.group_user')
        alice = new_test_user(self.env, login='caption_alice', name='Alice', groups='base.group_user')
        channel = self.env['discuss.channel'].with_user(bob)._get_or_create_chat(partners_to=alice.partner_id.ids)
        channel.sudo().channel_member_ids.filtered(lambda m: m.partner_id == bob.partner_id)._rtc_join_call()
        # no speech worker in tests: loading a model in the background is skipped
        with patch.object(stt_client, 'warm_up'):
            self.start_tour(f"/odoo/{channel.id}/action-mail.action_discuss?call=accept",
                            "meeting_transcription_summary.caption_lines", login='caption_alice')
