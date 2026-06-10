# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class JiraConnectorTestCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Param = cls.env['ir.config_parameter'].sudo()
        cls._set_jira_config(automatic=False, connection=False)
        cls.project = cls.env['project.project'].create({
            'name': 'Jira Test Project',
            'project_id_jira': 1001,
            'jira_project_key': 'JTP',
        })
        cls.task = cls.env['project.task'].create({
            'name': 'Jira Test Task',
            'project_id': cls.project.id,
            'task_id_jira': 'JTP-1',
        })

    @classmethod
    def _set_jira_config(cls, automatic=False, connection=False):
        cls.Param.set_param('odoo_jira_connector.url', 'https://jira.example.com/')
        cls.Param.set_param('odoo_jira_connector.user_id_jira', 'jira@example.com')
        cls.Param.set_param('odoo_jira_connector.api_token', 'token')
        cls.Param.set_param('odoo_jira_connector.automatic', automatic)
        cls.Param.set_param('odoo_jira_connector.connection', connection)


class TestJiraSprint(JiraConnectorTestCase):
    def setUp(self):
        super().setUp()
        self.sprint = self.env['jira.sprint'].create({
            'name': 'Sprint 1',
            'project_id': self.project.id,
        })

    def test_action_get_tasks(self):
        action = self.sprint.action_get_tasks()
        self.assertEqual(action['res_model'], 'project.task')
        self.assertIn(('sprint_id.state', '=', 'ongoing'), action['domain'])

    def test_action_get_backlogs(self):
        action = self.sprint.action_get_backlogs()
        self.assertEqual(action['name'], 'Backlogs')
        self.assertIn(('sprint_id.state', '=', 'to_start'), action['domain'])

    def test_action_get_all_tasks(self):
        action = self.sprint.action_get_all_tasks()
        self.assertEqual(action['name'], 'All Tasks')
        self.assertEqual(action['domain'], [('project_id', '=', self.project.id)])
