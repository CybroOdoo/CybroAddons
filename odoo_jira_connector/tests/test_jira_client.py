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
from odoo.addons.odoo_jira_connector.models.jira_client import (
    JiraClient, JiraError, adf_to_text, project_key_from_name)

from .common import JIRA_URL, JiraTestCommon, MockResponse, adf


class TestJiraClient(JiraTestCommon):

    def client(self):
        return JiraClient(JIRA_URL + '/', 'jira@example.com', 'token')

    def test_project_key_from_name(self):
        self.assertEqual(project_key_from_name('My Project'), 'MYP1ECT')
        self.assertEqual(project_key_from_name('ab'), 'ABP1ROJ')
        self.assertEqual(project_key_from_name('9 lives'), 'P9L1VES')
        self.assertEqual(project_key_from_name('Café Ops'), 'CAF1OPS')
        self.assertEqual(project_key_from_name(False), 'PPR1ROJ')

    def test_adf_to_text(self):
        body = {'type': 'doc', 'content': [
            {'type': 'paragraph', 'content': [
                {'type': 'text', 'text': 'Hello '},
                {'type': 'emoji', 'attrs': {'text': ':)'}},
            ]},
            {'type': 'mediaSingle', 'content': [{'type': 'media'}]},
        ]}
        self.assertEqual(adf_to_text(body), 'Hello :)')
        self.assertEqual(adf_to_text(adf('Plain')), 'Plain')
        self.assertEqual(adf_to_text(' wiki text '), 'wiki text')
        self.assertEqual(adf_to_text(None), '')

    def test_jira_error_uses_jira_messages(self):
        error = JiraError(MockResponse(
            {'errorMessages': ['Bad request.'], 'errors': {'projectKey': 'Key taken.'}},
            status_code=400))
        self.assertEqual(error.errors, {'projectKey': 'Key taken.'})
        self.assertIn('Bad request. Key taken.', str(error))
        error = JiraError(MockResponse(None, status_code=502))
        self.assertEqual(error.errors, {})
        self.assertIn('HTTP 502', str(error))

    def test_request_raises_on_error_status(self):
        with self.mock_jira({('GET', '/rest/api/2/project'): MockResponse({}, 401)}):
            with self.assertRaises(JiraError):
                self.client().get('/rest/api/2/project')

    def test_search_issues_follows_all_pages(self):
        def search(params, **kwargs):
            if params.get('nextPageToken') == 'page-2':
                return {'issues': [{'key': 'JTP-3'}], 'isLast': True}
            return {'issues': [{'key': 'JTP-1'}, {'key': 'JTP-2'}],
                    'nextPageToken': 'page-2', 'isLast': False}

        with self.mock_jira({('GET', '/rest/api/3/search/jql'): search}) as jira:
            issues = self.client().search_issues('project = "JTP"')
        self.assertEqual([issue['key'] for issue in issues], ['JTP-1', 'JTP-2', 'JTP-3'])
        first_call = jira.requests_to('GET', '/rest/api/3/search/jql')[0]
        self.assertEqual(first_call['params']['fields'], 'summary')

    def test_search_issues_falls_back_to_legacy_search(self):
        def legacy(params, **kwargs):
            if params['startAt'] == 0:
                return {'issues': [{'key': 'OLD-1'}, {'key': 'OLD-2'}], 'total': 3}
            return {'issues': [{'key': 'OLD-3'}], 'total': 3}

        with self.mock_jira({
            ('GET', '/rest/api/3/search/jql'): MockResponse({}, 404),
            ('GET', '/rest/api/2/search'): legacy,
        }):
            issues = self.client().search_issues('project = "OLD"')
        self.assertEqual([issue['key'] for issue in issues], ['OLD-1', 'OLD-2', 'OLD-3'])

    def test_search_issues_raises_other_errors(self):
        with self.mock_jira({('GET', '/rest/api/3/search/jql'): MockResponse({}, 500)}):
            with self.assertRaises(JiraError):
                self.client().search_issues('project = "JTP"')

    def test_download_only_sends_credentials_to_the_jira_site(self):
        with self.mock_jira({('GET', '/secure/file.txt'): MockResponse({}, content=b'abc')}):
            self.assertEqual(self.client().download(JIRA_URL + '/secure/file.txt'), b'abc')
            with self.assertRaises(ValueError):
                self.client().download('https://attacker.example.com/file.txt')

    def test_users_follows_all_pages(self):
        def users(params, **kwargs):
            return [{'accountId': 'a'}, {'accountId': 'b'}] if params['startAt'] == 0 else []

        with self.mock_jira({('GET', '/rest/api/2/users/search'): users}):
            self.assertEqual(len(self.client().users()), 2)

    def test_write_helpers_return_jira_ids(self):
        with self.mock_jira({
            ('POST', '/rest/api/3/issue/JTP-1/comment'): {'id': '10'},
            ('POST', '/rest/api/3/issue/JTP-1/attachments'): [{'id': '11'}],
            ('POST', '/rest/api/3/user'): {'accountId': 'acc-1'},
            ('GET', '/rest/api/2/issue/JTP-1'): {'fields': {'attachment': [{'id': '12'}]}},
        }) as jira:
            client = self.client()
            self.assertEqual(client.add_comment('JTP-1', 'Hi'), 10)
            self.assertEqual(client.upload_attachment('JTP-1', 'a.txt', b'x'), 11)
            self.assertEqual(client.create_user('a@example.com', 'A'), 'acc-1')
            self.assertEqual(client.attachments('JTP-1'), [{'id': '12'}])
            client.put('/rest/api/2/issue/JTP-1', {'fields': {}})
            client.delete('/rest/api/2/issue/JTP-1')
        comment = jira.requests_to('POST', '/rest/api/3/issue/JTP-1/comment')[0]
        self.assertEqual(comment['json'], {'body': adf('Hi')})
        self.assertEqual(len(jira.requests_to('DELETE')), 1)

    def test_client_factories_follow_settings(self):
        self.assertTrue(JiraClient.from_settings(self.env))
        self.assertIsNone(JiraClient.for_automatic_sync(self.env))
        self.set_jira_config(automatic=True)
        client = JiraClient.for_automatic_sync(self.env)
        self.assertEqual(client.base_url, JIRA_URL)
        self.assertIsNone(JiraClient.for_automatic_sync(
            self.env(context={'jira_skip_sync': True})))
        self.Param.set_param('odoo_jira_connector.url', False)
        self.assertIsNone(JiraClient.from_settings(self.env))
