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


class TestAIChatSession(AIConnectorAgentTestCase):
    def test_get_or_create_session_reuses_active_session(self):
        session_model = self.env["ai.chat.session"]
        first_session = session_model.get_or_create_session(self.provider.id, self.model.id, self.env.user.id)
        second_session = session_model.get_or_create_session(self.provider.id, self.model.id, self.env.user.id)

        self.assertEqual(first_session, second_session)
        self.assertEqual(first_session.ai_agent_id, self.provider)
        self.assertEqual(first_session.ai_model_id, self.model)
        self.assertIn(self.provider.name, first_session.name)
        self.assertIn(self.model.modelId, first_session.name)