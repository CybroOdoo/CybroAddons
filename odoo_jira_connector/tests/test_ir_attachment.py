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
from .common import LOGGER, JiraTestCommon, MockResponse


class TestIrAttachment(JiraTestCommon):

    def attach(self, task, name='document.pdf', **values):
        return self.env['ir.attachment'].create(dict({
            'name': name, 'raw': b'data', 'mimetype': 'application/pdf',
            'res_model': 'project.task', 'res_id': task.id}, **values))

    def test_create_uploads_attachment_of_synced_task(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('POST', '/rest/api/3/issue/JTP-1/attachments'): [{'id': '701'}]}) as jira:
            attachment = self.attach(self.task)
        self.assertEqual(attachment.attachment_id_jira, 701)
        upload = jira.requests_to('POST')[0]
        self.assertEqual(upload['files']['file'], ('document.pdf', b'data', 'application/pdf'))

    def test_create_skips_unsynced_tasks_and_jira_attachments(self):
        local_task = self.env['project.task'].create({
            'name': 'Local Task', 'project_id': self.project.id})
        self.set_jira_config(automatic=True)
        with self.mock_jira() as jira:
            self.attach(local_task)
            self.attach(self.task, attachment_id_jira=702)
            self.env['ir.attachment'].create({'name': 'other.txt', 'raw': b'x'})
        self.assertFalse(jira.calls)

    def test_create_keeps_attachment_when_upload_fails(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('POST', '/rest/api/3/issue/JTP-1/attachments'):
                             MockResponse({}, 413)}), self.assertLogs(LOGGER, 'ERROR'):
            attachment = self.attach(self.task)
        self.assertTrue(attachment.exists())
        self.assertFalse(attachment.attachment_id_jira)

    def test_unlink_deletes_jira_attachment(self):
        attachment = self.attach(self.task, attachment_id_jira=702)
        self.set_jira_config(automatic=True)
        with self.mock_jira() as jira:
            attachment.unlink()
        self.assertEqual(len(jira.requests_to('DELETE', '/rest/api/3/attachment/702')), 1)

    def test_unlink_logs_jira_errors(self):
        attachment = self.attach(self.task, attachment_id_jira=703)
        self.set_jira_config(automatic=True)
        with self.mock_jira({('DELETE', '/rest/api/3/attachment/703'): MockResponse({}, 404)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            attachment.unlink()
        self.assertFalse(attachment.exists())
