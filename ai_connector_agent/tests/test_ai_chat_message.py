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

from .common import AIConnectorAgentTestCase


class TestAIChatMessage(AIConnectorAgentTestCase):
    def test_create_updates_session_last_message_date(self):
        session = self.env["ai.chat.session"].create({
            "name": "Session",
            "ai_agent_id": self.provider.id,
            "ai_model_id": self.model.id,
            "user_id": self.env.user.id,
        })

        message = self.env["ai.chat.message"].create({
            "session_id": session.id,
            "message_type": "user",
            "content": "Hello",
        })

        self.assertEqual(session.last_message_date, message.timestamp)
