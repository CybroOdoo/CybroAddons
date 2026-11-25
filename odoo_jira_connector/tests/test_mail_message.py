# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from .common import LOGGER, JiraTestCommon, MockResponse, adf


class TestMailMessage(JiraTestCommon):

    def test_create_posts_task_comment_to_jira(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('POST', '/rest/api/3/issue/JTP-1/comment'): {'id': '501'}}) as jira:
            message = self.task.message_post(body='New comment', message_type='comment')
        self.assertEqual(message.message_id_jira, 501)
        posted = jira.requests_to('POST', '/rest/api/3/issue/JTP-1/comment')
        self.assertEqual([call['json'] for call in posted], [{'body': adf('New comment')}])

    def test_create_skips_messages_not_to_sync(self):
        local_task = self.env['project.task'].create({
            'name': 'Local Task', 'project_id': self.project.id})
        self.set_jira_config(automatic=True)
        with self.mock_jira() as jira:
            local_task.message_post(body='Local only', message_type='comment')
            self.task.message_post(body='System note', message_type='notification')
            self.task.message_post(body='', message_type='comment')
            self.env['mail.message'].create({
                'body': 'From Jira', 'model': 'project.task', 'res_id': self.task.id,
                'message_id_jira': 9})
        self.assertFalse(jira.calls)

    def test_create_logs_jira_errors(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('POST', '/rest/api/3/issue/JTP-1/comment'): MockResponse({}, 400)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            message = self.task.message_post(body='Rejected', message_type='comment')
        self.assertFalse(message.message_id_jira)
