# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from odoo.tests.common import TransactionCase

class TestProjectTask(TransactionCase):
    """
    Test suite for the extended project.task model.
    """
    
    def setUp(self):
        """
        Set up the test environment with a mock repository, project, issue, and task.
        """
        super(TestProjectTask, self).setUp()
        self.repository = self.env['github.repository'].create({
            'name': 'test-repo',
            'owner': 'test-owner',
        })
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
            'github_repository_id': self.repository.id,
        })
        self.issue = self.env['github.issue'].create({
            'repository_id': self.repository.id,
            'github_id': 'issue-1',
            'title': 'Test Issue',
            'state': 'open'
        })
        self.task = self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.project.id,
            'github_issue_id': self.issue.id,
        })

    def test_01_task_github_linking(self):
        """Test task linked to github issue"""
        self.assertEqual(self.task.github_issue_id, self.issue)
        self.assertEqual(self.task.repository_id, self.repository)

    def test_02_compute_commits_count(self):
        """Test compute commits count for task"""
        self.task._compute_commits_count()
        self.assertEqual(self.task.commits_count, 0)
