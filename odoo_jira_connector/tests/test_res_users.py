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
from odoo.fields import Command

from .common import LOGGER, JiraTestCommon, MockResponse


class TestResUsers(JiraTestCommon):

    def create_user(self, login, **values):
        return self.env['res.users'].with_context(no_reset_password=True).create(
            dict({'name': login, 'login': login}, **values))

    def test_create_exports_internal_email_user(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('POST', '/rest/api/3/user'): {'accountId': 'account-1'}}) as jira:
            user = self.create_user('jira.export.user@example.com')
        self.assertEqual(user.jira_user_key, 'account-1')
        self.assertEqual(jira.requests_to('POST')[0]['json']['emailAddress'],
                         'jira.export.user@example.com')

    def test_create_skips_users_not_to_export(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira() as jira:
            self.create_user('not-an-email-login')
            self.create_user('portal.user@example.com', group_ids=[
                Command.set([self.env.ref('base.group_portal').id])])
            self.create_user('mapped.user@example.com', jira_user_key='known')
        self.assertFalse(jira.calls)

    def test_create_logs_jira_errors(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('POST', '/rest/api/3/user'): MockResponse({}, 403)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            user = self.create_user('refused.user@example.com')
        self.assertFalse(user.jira_user_key)
