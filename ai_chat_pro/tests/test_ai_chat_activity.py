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

from datetime import date, timedelta

from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAiChatActivity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(cls.env, login='ai_activity_user', groups='base.group_user,ai_chat_pro.group_ai_chat_user')
        cls.other_user = new_test_user(cls.env, login='ai_activity_other', groups='base.group_user,ai_chat_pro.group_ai_chat_user')
        cls.conversation = cls.env['ai.chat.conversation'].with_user(cls.user).create({'name': "Chair sales"})
        Message = cls.env['ai.chat.message'].sudo()
        Message.create({'conversation_id': cls.conversation.id, 'role': 'user', 'content': "How can I sell more chairs?"})
        cls.message = Message.create({
            'conversation_id': cls.conversation.id, 'role': 'assistant', 'content': "Bundle them", 'source': 'deep',
            'result': {
                'type': 'analysis', 'verdict': "Bundle chairs with desks.", 'confidence': 'medium', 'summary': "",
                'findings': [], 'recommendations': [], 'risks': [],
                'next_steps': ["Set the bundle price this week", "Review the results in 30 days"],
            },
        })
        cls.Conversation = cls.env['ai.chat.conversation'].with_user(cls.user)

    def _plan(self, index=0, **values):
        defaults = self.Conversation.get_next_step_activity_defaults(self.message.id, index)
        return self.Conversation.create_next_step_activity(self.message.id, index, {
            'summary': defaults['summary'], 'activity_type_id': defaults['activity_type_id'], **values,
        })

    def test_defaults(self):
        defaults = self.Conversation.get_next_step_activity_defaults(self.message.id, 1)
        self.assertEqual(defaults['summary'], "Review the results in 30 days")
        self.assertEqual(defaults['activity_type_id'], self.env.ref('mail.mail_activity_data_todo').id)
        types = self.env['mail.activity.type'].browse([t['id'] for t in defaults['activity_types']])
        self.assertFalse(types.filtered('res_model'), "only types that need no record are offered")
        self.assertTrue(all(t['date_deadline'] for t in defaults['activity_types']))

    def test_plan_next_step(self):
        deadline = date.today() + timedelta(days=5)
        values = self._plan(0, summary="Price the chair bundle", date_deadline=str(deadline))
        activity = self.env['mail.activity'].search([('user_id', '=', self.user.id), ('summary', '=', "Price the chair bundle")])
        self.assertEqual(len(activity), 1)
        self.assertFalse(activity.res_model, "a free activity: conversations are private")
        self.assertEqual(activity.date_deadline, deadline)
        self.assertIn("How can I sell more chairs?", activity.note)
        self.assertIn("Bundle chairs with desks.", activity.note)
        self.assertIn(f"/odoo/action-ai_chat_pro.ai_chat_action_client?active_id={self.conversation.id}", activity.note)
        planned = values['result']['next_step_activities']
        self.assertEqual(list(planned), ['0'])
        self.assertEqual((planned['0']['id'], planned['0']['state']), (activity.id, 'planned'))
        # shown when the conversation is opened again
        data = self.Conversation.get_chat_data(self.conversation.id)
        self.assertEqual(data['conversation']['messages'][1]['result']['next_step_activities']['0']['id'], activity.id)

        with self.assertRaisesRegex(UserError, "already planned"):
            self._plan(0)

        # marked as done in Odoo: shown as done
        activity.with_user(self.user).action_feedback(feedback="Done")
        values = self.message.with_user(self.user)._get_chat_values()
        self.assertEqual(values['result']['next_step_activities']['0']['state'], 'done')

    def test_removed_activity_can_be_planned_again(self):
        values = self._plan(1)
        self.env['mail.activity'].browse(values['result']['next_step_activities']['1']['id']).unlink()
        self.assertFalse(self.message.with_user(self.user)._get_chat_values()['result']['next_step_activities'])
        self.assertTrue(self._plan(1)['result']['next_step_activities']['1'])

    def test_checks(self):
        with self.assertRaises(AccessError):
            self.env['ai.chat.conversation'].with_user(self.other_user).get_next_step_activity_defaults(self.message.id, 0)
        with self.assertRaisesRegex(UserError, "no such next step"):
            self.Conversation.get_next_step_activity_defaults(self.message.id, 5)
        question = self.conversation.message_ids.filtered(lambda m: m.role == 'user')
        with self.assertRaisesRegex(UserError, "no such next step"):
            self.Conversation.get_next_step_activity_defaults(question.id, 0)
        with self.assertRaisesRegex(UserError, "type of activity"):
            self.Conversation.create_next_step_activity(self.message.id, 0, {'activity_type_id': 0})
