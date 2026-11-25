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
from .common import JiraTestCommon


class TestJiraSprint(JiraTestCommon):

    def setUp(self):
        super().setUp()
        self.sprint = self.env['jira.sprint'].create({
            'name': 'Sprint 1', 'project_id': self.project.id})

    def test_action_get_tasks(self):
        action = self.sprint.action_get_tasks()
        self.assertEqual(action['res_model'], 'project.task')
        self.assertIn(('sprint_id.state', '=', 'ongoing'), action['domain'])
        self.assertEqual(action['views'][1], [False, 'list'])

    def test_action_get_backlogs(self):
        action = self.sprint.action_get_backlogs()
        self.assertEqual(action['name'], 'Backlogs')
        self.assertIn(('sprint_id.state', '=', 'to_start'), action['domain'])

    def test_action_get_all_tasks(self):
        action = self.sprint.action_get_all_tasks()
        self.assertEqual(action['name'], 'All Tasks')
        self.assertEqual(action['domain'], [('project_id', '=', self.project.id)])
