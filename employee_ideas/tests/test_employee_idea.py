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
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestEmployeeIdea(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestEmployeeIdea, cls).setUpClass()

        # Create departments
        cls.dept_it = cls.env['hr.department'].create({
            'name': 'IT Department',
        })
        cls.dept_hr = cls.env['hr.department'].create({
            'name': 'HR Department',
        })

        # Create users
        cls.user_creator = cls.env['res.users'].create({
            'name': 'Idea Creator',
            'login': 'creator',
            'email': 'creator@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('hr.group_hr_user').id])],
        })
        cls.user_voter = cls.env['res.users'].create({
            'name': 'Idea Voter',
            'login': 'voter',
            'email': 'voter@example.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('hr.group_hr_user').id])],
        })
        cls.user_hr = cls.env['res.users'].create({
            'name': 'HR Officer',
            'login': 'hr_officer',
            'email': 'hr@example.com',
            'group_ids': [(6, 0, [cls.env.ref('hr.group_hr_user').id])],
        })

        # Create employees linked to users
        cls.employee_creator = cls.env['hr.employee'].create({
            'name': 'Idea Creator Employee',
            'user_id': cls.user_creator.id,
            'department_id': cls.dept_it.id,
        })
        cls.employee_voter = cls.env['hr.employee'].create({
            'name': 'Idea Voter Employee',
            'user_id': cls.user_voter.id,
            'department_id': cls.dept_it.id,
        })
        cls.employee_hr = cls.env['hr.employee'].create({
            'name': 'HR Officer Employee',
            'user_id': cls.user_hr.id,
            'department_id': cls.dept_hr.id,
        })

        # Create idea types
        cls.idea_type_it = cls.env['idea.type'].create({
            'name': 'IT Ideas',
            'minimum_vote': 2,
            'hr_department_ids': [(6, 0, [cls.dept_it.id])],
        })
        cls.idea_type_general = cls.env['idea.type'].create({
            'name': 'General Ideas',
            'minimum_vote': 1,
            'hr_department_ids': [(6, 0, [cls.dept_it.id, cls.dept_hr.id])],
        })

    def test_01_employee_idea_creation(self):
        """Test creation of an employee idea and default values."""
        # Create as user_creator
        idea = self.env['employee.idea'].with_user(self.user_creator).create({
            'title': 'New Coffee Machine',
            'idea_type_id': self.idea_type_it.id,
            'details': 'Need coffee machine for developers.',
        })

        self.assertEqual(idea.employee_id, self.employee_creator, "Employee should default to the current user's employee record")
        self.assertNotEqual(idea.reference_no, 'New', "Reference number should be generated from sequence")
        self.assertEqual(idea.state, 'draft', "Initial state should be draft")
        self.assertEqual(idea.vote_count, 0, "Initial vote count should be 0")
        self.assertEqual(idea.have_minimum_vote, 'Does not have minimum vote', "Should indicate it does not have minimum votes")

    def test_02_idea_type_domain(self):
        """Test the get_idea_type_domain function filters types correctly by department."""
        # For IT creator (in IT department)
        domain = self.env['employee.idea'].with_user(self.user_creator).get_idea_type_domain()
        idea_type_ids = self.env['idea.type'].search(domain)
        self.assertIn(self.idea_type_it, idea_type_ids, "IT user should see IT Ideas type")
        self.assertIn(self.idea_type_general, idea_type_ids, "IT user should see General Ideas type")

        # For HR user (in HR department)
        domain_hr = self.env['employee.idea'].with_user(self.user_hr).get_idea_type_domain()
        idea_type_ids_hr = self.env['idea.type'].search(domain_hr)
        self.assertNotIn(self.idea_type_it, idea_type_ids_hr, "HR user should not see IT Ideas type")
        self.assertIn(self.idea_type_general, idea_type_ids_hr, "HR user should see General Ideas type")

    def test_03_stage_transitions(self):
        """Test workflow transitions for approval, approve, and reject."""
        idea = self.env['employee.idea'].with_user(self.user_creator).create({
            'title': 'Office Upgrade',
            'idea_type_id': self.idea_type_general.id,
            'details': 'Standing desks for everyone.',
        })

        # Send for approval
        idea.action_send_approval()
        self.assertEqual(idea.state, 'approval', "State should change to approval")

        # Approve
        idea.action_approve()
        self.assertEqual(idea.state, 'post', "State should change to post")

        # Reject
        idea.action_reject()
        self.assertEqual(idea.state, 'rejected', "State should change to rejected")

    def test_04_button_visibilities(self):
        """Test visibility computes for Send Approval and Give Vote."""
        idea = self.env['employee.idea'].with_user(self.user_creator).create({
            'title': 'Team Outing',
            'idea_type_id': self.idea_type_it.id,
            'details': 'Annual team outing details.',
        })

        # Send approval visibility
        idea.with_user(self.user_creator)._compute_is_send_approval_visibility()
        self.assertTrue(idea.is_send_approval_visibility, "Creator should see the Send Approval button")

        # Transition to post to allow other users to read/access the idea
        idea.state = 'post'

        idea.with_user(self.user_voter)._compute_is_send_approval_visibility()
        # Since the record was created by self.user_creator (which was set in the environment or vals),
        # create_uid.id is user_creator.id (which is not user_voter.id).
        self.assertFalse(idea.is_send_approval_visibility, "Other users should not see the Send Approval button")

        # Give vote visibility
        # Creator should not be able to vote
        idea.with_user(self.user_creator)._compute_is_visible_give_vote()
        self.assertFalse(idea.is_visible_give_vote, "Creator cannot vote on their own idea")

        # Voter in IT department (allowed) should be able to vote
        idea.with_user(self.user_voter)._compute_is_visible_give_vote()
        self.assertTrue(idea.is_visible_give_vote, "Employee in allowed department should see Give Vote button")

        # HR User (not in IT department) should not see the button
        idea.with_user(self.user_hr)._compute_is_visible_give_vote()
        self.assertFalse(idea.is_visible_give_vote, "Employee in non-allowed department should not see Give Vote button")

    def test_05_voting_wizard_and_logic(self):
        """Test giving a vote and vote computation logic."""
        idea = self.env['employee.idea'].with_user(self.user_creator).create({
            'title': 'New IDE License',
            'idea_type_id': self.idea_type_it.id,
            'details': 'Need PyCharm licenses.',
        })

        # Transition to post so voters can access/vote
        idea.state = 'post'

        # Voter opens the vote wizard
        action = idea.with_user(self.user_voter).action_give_vote()
        self.assertEqual(action['res_model'], 'give.vote')

        wizard = self.env['give.vote'].browse(action['res_id'])
        self.assertEqual(wizard.employee_id, self.employee_voter)
        self.assertEqual(wizard.reference, idea.reference_no)

        # Voter votes
        wizard.with_user(self.user_voter).action_vote()
        self.assertTrue(wizard.is_vote)
        self.assertEqual(wizard.status, 'Voted')

        # Invalidate cache to force recomputation on next read under voter's context
        idea.invalidate_recordset()

        # Check that voter is registered as voted
        self.assertTrue(idea.with_user(self.user_voter).is_vote, "Voter should see they have voted")
        self.assertEqual(idea.vote_count, 1, "Vote count should be 1")
        self.assertEqual(idea.have_minimum_vote, 'Does not have minimum vote', "Should need 2 votes minimum")

        # Create another voter to reach minimum votes
        user_voter_2 = self.env['res.users'].create({
            'name': 'Idea Voter 2',
            'login': 'voter2',
            'email': 'voter2@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('hr.group_hr_user').id])],
        })
        self.env['hr.employee'].create({
            'name': 'Idea Voter 2 Employee',
            'user_id': user_voter_2.id,
            'department_id': self.dept_it.id,
        })

        # Voter 2 votes
        action2 = idea.with_user(user_voter_2).action_give_vote()
        wizard2 = self.env['give.vote'].browse(action2['res_id'])
        wizard2.with_user(user_voter_2).action_vote()

        idea.invalidate_recordset()
        self.assertEqual(idea.vote_count, 2, "Vote count should be 2")
        self.assertEqual(idea.have_minimum_vote, 'Go with this', "Minimum votes reached (2)")

    def test_06_comment_wizard(self):
        """Test wizard comment submission."""
        idea = self.env['employee.idea'].with_user(self.user_creator).create({
            'title': 'Snacks',
            'idea_type_id': self.idea_type_general.id,
            'details': 'Healthy snacks in pantry.',
        })

        # Transition to post so voters can access/comment
        idea.state = 'post'

        action = idea.with_user(self.user_voter).action_give_vote()
        wizard = self.env['give.vote'].browse(action['res_id'])

        # Submit comment without entering text should fail
        with self.assertRaises(ValidationError):
            wizard.with_user(self.user_voter).action_submit_comment()

        # Submit with comment
        wizard.comments = 'Great idea!'
        wizard.with_user(self.user_voter).action_submit_comment()
        self.assertEqual(wizard.status, 'Commented')

    def test_07_smart_buttons_and_actions(self):
        """Test actions returned by smart buttons on idea and idea type."""
        idea = self.env['employee.idea'].with_user(self.user_creator).create({
            'title': 'Smart buttons',
            'idea_type_id': self.idea_type_general.id,
            'details': 'Testing smart button actions.',
        })

        # Test smart button action for votes
        vote_action = idea.action_get_votes_of_idea()
        self.assertEqual(vote_action['res_model'], 'give.vote')
        self.assertEqual(vote_action['view_mode'], 'list')
        self.assertIn(('employee_ideas_id', '=', idea.id), vote_action['domain'])

        # Test smart button action for comments
        comment_action = idea.action_get_comments_of_idea()
        self.assertEqual(comment_action['res_model'], 'give.vote')
        self.assertIn(('status', '=', 'Commented'), comment_action['domain'])

        # Test smart button action on idea.type
        type_action = self.idea_type_general.action_get_the_ideas()
        self.assertEqual(type_action['res_model'], 'employee.idea')
        self.assertIn(('idea_type_id', '=', self.idea_type_general.id), type_action['domain'])

        # Test compute total_ideas on idea.type
        self.idea_type_general._compute_total_ideas()
        self.assertEqual(self.idea_type_general.total_ideas, 1)

    def test_08_print_report(self):
        """Test print action doesn't crash."""
        idea = self.env['employee.idea'].with_user(self.user_creator).create({
            'title': 'Print report',
            'idea_type_id': self.idea_type_general.id,
            'details': 'Testing printing logic.',
        })
        # Call print action
        report_action = idea.action_print()
        self.assertEqual(report_action['report_name'], 'employee_ideas.employee_idea_report')
