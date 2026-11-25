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
from odoo.exceptions import ValidationError

from .common import LOGGER, JiraTestCommon, MockResponse


class TestProjectProject(JiraTestCommon):

    def test_action_get_sprint_returns_project_sprint_action(self):
        action = self.project.action_get_sprint()
        self.assertEqual(action['res_model'], 'jira.sprint')
        self.assertEqual(action['context'], {'default_project_id': self.project.id})
        self.assertEqual(action['domain'], [('project_id', '=', self.project.id)])

    def test_create_does_not_call_jira_without_automatic_mode(self):
        with self.mock_jira() as jira:
            self.env['project.project'].create({'name': 'Local Project'})
        self.assertFalse(jira.calls)

    def test_create_exports_project_when_automatic_enabled(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({
            ('GET', '/rest/api/3/project'): [{'name': 'Other Jira Project'}],
            ('POST', '/rest/simplified/latest/project'): {'projectId': 2002, 'projectKey': 'NEW1ECT'},
        }) as jira:
            project = self.env['project.project'].create({'name': 'New Test Project'})
        self.assertEqual(project.project_id_jira, 2002)
        self.assertEqual(project.jira_project_key, 'NEW1ECT')
        payload = jira.requests_to('POST', '/rest/simplified/latest/project')[0]['json']
        self.assertEqual(payload['key'], 'NEW1ECT')

    def test_create_skips_names_already_in_jira(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('GET', '/rest/api/3/project'): [{'name': 'In Jira'}]}) as jira:
            project = self.env['project.project'].create({'name': 'In Jira'})
        self.assertFalse(project.project_id_jira)
        self.assertFalse(jira.requests_to('POST'))

    def test_create_reports_jira_validation_errors(self):
        self.set_jira_config(automatic=True)
        for field in ('projectName', 'projectKey'):
            with self.mock_jira({
                ('GET', '/rest/api/3/project'): [],
                ('POST', '/rest/simplified/latest/project'): MockResponse(
                    {'errors': {field: 'Rejected by Jira.'}}, 400),
            }), self.assertRaises(ValidationError):
                self.env['project.project'].create({'name': 'Rejected Project'})

    def test_create_logs_other_jira_errors(self):
        self.set_jira_config(automatic=True)
        for answer in (MockResponse({}, 500), {'unexpected': True}):
            with self.mock_jira({
                ('GET', '/rest/api/3/project'): MockResponse({}, 500),
                ('POST', '/rest/simplified/latest/project'): answer,
            }), self.assertLogs(LOGGER, 'ERROR'):
                project = self.env['project.project'].create({'name': 'Unlucky Project'})
            self.assertFalse(project.project_id_jira)

    def test_write_renames_jira_project(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira() as jira:
            self.project.write({'name': 'Renamed Project'})
            self.project.write({'name': 'Renamed Project'})
        puts = jira.requests_to('PUT', '/rest/api/3/project/JTP')
        self.assertEqual([call['json'] for call in puts], [{'name': 'Renamed Project'}])

    def test_write_logs_rename_errors(self):
        self.set_jira_config(automatic=True)
        with self.mock_jira({('PUT', '/rest/api/3/project/JTP'): MockResponse({}, 403)}), \
                self.assertLogs(LOGGER, 'ERROR'):
            self.project.write({'name': 'Forbidden Rename'})
        self.assertEqual(self.project.name, 'Forbidden Rename')
