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
#############################################################################
from psycopg2 import IntegrityError
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import HttpCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestDiscussPoll(HttpCase):
    """Test suite for Odoo Poll functionality and constraints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Standard internal user (no poll creation permission)
        cls.internal_user = cls.env['res.users'].create({
            'name': 'Test Internal User',
            'login': 'test_internal_user@example.com',
            'email': 'test_internal_user@example.com',
            'password': 'test_internal_user',
            'company_id': cls.company.id,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Poll user
        cls.poll_user = cls.env['res.users'].create({
            'name': 'Test Poll User',
            'login': 'test_poll_user@example.com',
            'email': 'test_poll_user@example.com',
            'password': 'test_poll_user',
            'company_id': cls.company.id,
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_poll.group_odoo_poll_user').id,
            ])],
        })

        # Second poll user
        cls.poll_user_2 = cls.env['res.users'].create({
            'name': 'Test Poll User 2',
            'login': 'test_poll_user_2@example.com',
            'email': 'test_poll_user_2@example.com',
            'password': 'test_poll_user_2',
            'company_id': cls.company.id,
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_poll.group_odoo_poll_user').id,
            ])],
        })

        # Poll manager
        cls.poll_manager = cls.env['res.users'].create({
            'name': 'Test Poll Manager',
            'login': 'test_poll_manager@example.com',
            'email': 'test_poll_manager@example.com',
            'password': 'test_poll_manager',
            'company_id': cls.company.id,
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('odoo_poll.group_odoo_poll_manager').id,
            ])],
        })

        # If mail_message_access is installed, grant chatter message permission
        chatter_send_group = cls.env.ref('mail_message_access.group_allow_send_message_btn', raise_if_not_found=False)
        if chatter_send_group:
            cls.poll_user.write({'group_ids': [(4, chatter_send_group.id)]})
            cls.poll_user_2.write({'group_ids': [(4, chatter_send_group.id)]})
            cls.poll_manager.write({'group_ids': [(4, chatter_send_group.id)]})
            cls.internal_user.write({'group_ids': [(4, chatter_send_group.id)]})


    def test_01_create_poll_success(self):
        """Test creating a poll with valid options."""
        poll = self.env['discuss.poll'].with_user(self.poll_user).create({
            'question': 'What is your preferred development OS?',
            'is_multiple_choice': False,
            'option_ids': [
                (0, 0, {'name': 'Linux', 'sequence': 1}),
                (0, 0, {'name': 'macOS', 'sequence': 2}),
                (0, 0, {'name': 'Windows', 'sequence': 3}),
            ],
        })
        self.assertEqual(poll.question, 'What is your preferred development OS?')
        self.assertEqual(len(poll.option_ids), 3)
        self.assertEqual(poll.total_votes, 0)
        self.assertFalse(poll.is_closed)

    def test_02_poll_minimum_options_constraint(self):
        """Test that a poll with fewer than 2 options raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.env['discuss.poll'].with_user(self.poll_user).create({
                'question': 'Poll with only one option?',
                'option_ids': [
                    (0, 0, {'name': 'Only Option', 'sequence': 1}),
                ],
            })

    def test_03_single_choice_voting_and_replacement(self):
        """Test voting in single choice poll and vote replacement."""
        poll = self.env['discuss.poll'].with_user(self.poll_user).create({
            'question': 'Choose one fruit:',
            'is_multiple_choice': False,
            'option_ids': [
                (0, 0, {'name': 'Apple', 'sequence': 1}),
                (0, 0, {'name': 'Banana', 'sequence': 2}),
            ],
        })
        opt_apple = poll.option_ids[0]
        opt_banana = poll.option_ids[1]

        # Vote for Apple
        vote1 = self.env['poll.vote'].with_user(self.poll_user).create({
            'poll_id': poll.id,
            'option_id': opt_apple.id,
            'voter_id': self.poll_user.partner_id.id,
        })
        self.assertEqual(poll.total_votes, 1)
        self.assertEqual(opt_apple.vote_count, 1)
        self.assertEqual(opt_banana.vote_count, 0)

        # Attempting to create a second vote for Banana without removing Apple raises ValidationError
        with self.assertRaises(ValidationError):
            self.env['poll.vote'].with_user(self.poll_user).create({
                'poll_id': poll.id,
                'option_id': opt_banana.id,
                'voter_id': self.poll_user.partner_id.id,
            })

        # Remove previous vote and vote for Banana
        vote1.unlink()
        self.env['poll.vote'].with_user(self.poll_user).create({
            'poll_id': poll.id,
            'option_id': opt_banana.id,
            'voter_id': self.poll_user.partner_id.id,
        })
        self.assertEqual(poll.total_votes, 1)
        self.assertEqual(opt_apple.vote_count, 0)
        self.assertEqual(opt_banana.vote_count, 1)

    def test_04_multiple_choice_voting(self):
        """Test voting in multiple choice poll through the controller endpoint."""
        poll = self.env['discuss.poll'].with_user(self.poll_user).create({
            'question': 'Select programming languages you use:',
            'is_multiple_choice': True,
            'option_ids': [
                (0, 0, {'name': 'Python', 'sequence': 1}),
                (0, 0, {'name': 'JavaScript', 'sequence': 2}),
                (0, 0, {'name': 'Rust', 'sequence': 3}),
            ],
        })
        opt_py = poll.option_ids[0]
        opt_js = poll.option_ids[1]

        self.authenticate(self.poll_user.login, 'test_poll_user')

        # 1. Voter selects Python: JS sends [opt_py.id]
        res1 = self.make_jsonrpc_request('/discuss/poll/vote', {
            'poll_id': poll.id,
            'option_ids': [opt_py.id],
        })
        self.assertNotIn('error', res1)
        self.assertEqual(res1['total_votes'], 1)
        self.assertEqual(res1['user_votes'], [opt_py.id])

        # 2. Voter selects JavaScript as well: JS resends ALL selected options [opt_py.id, opt_js.id]
        # Previously, this raised a unique constraint error because it tried to re-create opt_py
        res2 = self.make_jsonrpc_request('/discuss/poll/vote', {
            'poll_id': poll.id,
            'option_ids': [opt_py.id, opt_js.id],
        })
        self.assertNotIn('error', res2)
        self.assertEqual(res2['total_votes'], 1)
        self.assertCountEqual(res2['user_votes'], [opt_py.id, opt_js.id])
        self.assertEqual(opt_py.vote_count, 1)
        self.assertEqual(opt_js.vote_count, 1)

        # 3. Voter deselects Python: JS resends [opt_js.id]
        # The controller must remove opt_py vote and keep opt_js vote
        res3 = self.make_jsonrpc_request('/discuss/poll/vote', {
            'poll_id': poll.id,
            'option_ids': [opt_js.id],
        })
        self.assertNotIn('error', res3)
        self.assertEqual(res3['total_votes'], 1)
        self.assertEqual(res3['user_votes'], [opt_js.id])
        self.assertEqual(opt_py.vote_count, 0)
        self.assertEqual(opt_js.vote_count, 1)

    def test_05_duplicate_option_vote_constraint(self):
        """Test that voting for the same option twice raises ValidationError."""
        poll = self.env['discuss.poll'].with_user(self.poll_user).create({
            'question': 'Select favorite:',
            'is_multiple_choice': True,
            'option_ids': [
                (0, 0, {'name': 'Option 1', 'sequence': 1}),
                (0, 0, {'name': 'Option 2', 'sequence': 2}),
            ],
        })
        opt1 = poll.option_ids[0]

        self.env['poll.vote'].with_user(self.poll_user).create({
            'poll_id': poll.id,
            'option_id': opt1.id,
            'voter_id': self.poll_user.partner_id.id,
        })

        with mute_logger('odoo.sql_db'), self.assertRaises((ValidationError, IntegrityError)):
            self.env['poll.vote'].with_user(self.poll_user).create({
                'poll_id': poll.id,
                'option_id': opt1.id,
                'voter_id': self.poll_user.partner_id.id,
            })


    def test_06_close_and_reopen_poll(self):
        """Test closing poll prevents voting and reopening allows it."""
        poll = self.env['discuss.poll'].with_user(self.poll_user).create({
            'question': 'Meeting tomorrow?',
            'is_multiple_choice': False,
            'option_ids': [
                (0, 0, {'name': 'Yes', 'sequence': 1}),
                (0, 0, {'name': 'No', 'sequence': 2}),
            ],
        })
        opt_yes = poll.option_ids[0]

        poll.action_close()
        self.assertTrue(poll.is_closed)

        with self.assertRaises(ValidationError):
            self.env['poll.vote'].with_user(self.poll_user).create({
                'poll_id': poll.id,
                'option_id': opt_yes.id,
                'voter_id': self.poll_user.partner_id.id,
            })

        poll.action_reopen()
        self.assertFalse(poll.is_closed)

        vote = self.env['poll.vote'].with_user(self.poll_user).create({
            'poll_id': poll.id,
            'option_id': opt_yes.id,
            'voter_id': self.poll_user.partner_id.id,
        })
        self.assertTrue(vote.id)

    def test_07_get_results_computation(self):
        """Test get_results calculation for counts and percentages."""
        poll = self.env['discuss.poll'].with_user(self.poll_user).create({
            'question': 'Frontend framework?',
            'is_multiple_choice': False,
            'option_ids': [
                (0, 0, {'name': 'Owl', 'sequence': 1}),
                (0, 0, {'name': 'Vue', 'sequence': 2}),
            ],
        })
        opt_owl = poll.option_ids[0]
        opt_vue = poll.option_ids[1]

        self.env['poll.vote'].with_user(self.poll_user).create({
            'poll_id': poll.id,
            'option_id': opt_owl.id,
            'voter_id': self.poll_user.partner_id.id,
        })
        self.env['poll.vote'].with_user(self.poll_user_2).create({
            'poll_id': poll.id,
            'option_id': opt_vue.id,
            'voter_id': self.poll_user_2.partner_id.id,
        })

        results = poll.with_user(self.poll_user).get_results()
        self.assertEqual(results['total_votes'], 2)
        self.assertTrue(results['is_author'])
        self.assertEqual(results['user_votes'], [opt_owl.id])

        opt_results = {o['id']: o for o in results['options']}
        self.assertEqual(opt_results[opt_owl.id]['percentage'], 50.0)
        self.assertEqual(opt_results[opt_vue.id]['percentage'], 50.0)

    def test_08_security_access_rights(self):
        """Test security access rights across standard, poll user, and manager."""
        # Standard user without group_odoo_poll_user cannot create a poll
        with self.assertRaises(AccessError):
            self.env['discuss.poll'].with_user(self.internal_user).create({
                'question': 'Can I create a poll?',
                'option_ids': [
                    (0, 0, {'name': 'Yes'}),
                    (0, 0, {'name': 'No'}),
                ],
            })

        # Standard user CAN vote on an existing poll
        poll = self.env['discuss.poll'].with_user(self.poll_user).create({
            'question': 'Company lunch option?',
            'option_ids': [
                (0, 0, {'name': 'Pizza'}),
                (0, 0, {'name': 'Sushi'}),
            ],
        })
        vote = self.env['poll.vote'].with_user(self.internal_user).create({
            'poll_id': poll.id,
            'option_id': poll.option_ids[0].id,
            'voter_id': self.internal_user.partner_id.id,
        })
        self.assertTrue(vote.id)

        # Security rule: Users cannot delete or modify other users' polls
        poll_user_2_poll = self.env['discuss.poll'].with_user(self.poll_user_2).create({
            'question': 'User 2 Poll',
            'option_ids': [
                (0, 0, {'name': 'Opt A'}),
                (0, 0, {'name': 'Opt B'}),
            ],
        })
        with self.assertRaises(AccessError):
            poll_user_2_poll.with_user(self.poll_user).write({'question': 'Hacked Question'})
        with self.assertRaises(AccessError):
            poll_user_2_poll.with_user(self.poll_user).unlink()

        # Security rule: Users cannot delete other users' votes
        user_2_vote = self.env['poll.vote'].with_user(self.poll_user_2).create({
            'poll_id': poll.id,
            'option_id': poll.option_ids[1].id,
            'voter_id': self.poll_user_2.partner_id.id,
        })
        with self.assertRaises(AccessError):
            user_2_vote.with_user(self.poll_user).unlink()

        # User CAN delete their own vote
        user_2_vote.with_user(self.poll_user_2).unlink()
        self.assertFalse(user_2_vote.exists())

        # Poll manager can close the poll created by another user
        poll.with_user(self.poll_manager).action_close()
        self.assertTrue(poll.is_closed)

        # Poll manager can unlink other users' polls
        poll_user_2_poll.with_user(self.poll_manager).unlink()
        self.assertFalse(poll_user_2_poll.exists())

    def test_09_controller_endpoints_full_flow(self):
        """Test all controller RPC endpoints."""
        channel = self.env['discuss.channel'].create({
            'name': 'Poll Discussion Channel',
            'channel_member_ids': [
                (0, 0, {'partner_id': self.poll_user.partner_id.id}),
                (0, 0, {'partner_id': self.poll_user_2.partner_id.id}),
            ],
        })

        # Authenticate as poll user
        self.authenticate(self.poll_user.login, 'test_poll_user')

        # 1. /discuss/poll/create
        create_res = self.make_jsonrpc_request('/discuss/poll/create', {
            'thread_id': channel.id,
            'thread_model': 'discuss.channel',
            'question': 'Which cloud provider do you prefer?',
            'options': ['GCP', 'AWS', 'Azure'],
            'is_multiple_choice': False,
        })
        self.assertIn('poll_id', create_res)
        poll_id = create_res['poll_id']
        poll = self.env['discuss.poll'].browse(poll_id)
        self.assertEqual(len(poll.option_ids), 3)
        self.assertEqual(poll.question, 'Which cloud provider do you prefer?')
        opt_gcp = poll.option_ids.filtered(lambda o: o.name == 'GCP')
        opt_aws = poll.option_ids.filtered(lambda o: o.name == 'AWS')

        # 2. /discuss/poll/vote (single choice)
        vote_res = self.make_jsonrpc_request('/discuss/poll/vote', {
            'poll_id': poll_id,
            'option_ids': [opt_gcp.id],
        })
        self.assertEqual(vote_res['total_votes'], 1)
        self.assertEqual(vote_res['user_votes'], [opt_gcp.id])

        # Vote change: Switch to AWS (replaces GCP without constraint violation)
        vote_res2 = self.make_jsonrpc_request('/discuss/poll/vote', {
            'poll_id': poll_id,
            'option_ids': [opt_aws.id],
        })
        self.assertEqual(vote_res2['total_votes'], 1)
        self.assertEqual(vote_res2['user_votes'], [opt_aws.id])
        self.assertEqual(opt_gcp.vote_count, 0)
        self.assertEqual(opt_aws.vote_count, 1)

        # 3. /discuss/poll/vote with invalid option
        invalid_vote_res = self.make_jsonrpc_request('/discuss/poll/vote', {
            'poll_id': poll_id,
            'option_ids': [999999],
        })
        self.assertIn('error', invalid_vote_res)
        self.assertEqual(invalid_vote_res['error'], 'Invalid option selected')

        # 4. /discuss/poll/results
        results_res = self.make_jsonrpc_request('/discuss/poll/results', {
            'poll_id': poll_id,
        })
        self.assertEqual(results_res['total_votes'], 1)
        self.assertEqual(results_res['user_votes'], [opt_aws.id])

        # 5. /discuss/poll/close by unauthorized user
        self.authenticate(self.poll_user_2.login, 'test_poll_user_2')
        unauth_close = self.make_jsonrpc_request('/discuss/poll/close', {
            'poll_id': poll_id,
        })
        self.assertIn('error', unauth_close)
        self.assertEqual(unauth_close['error'], 'Only poll author or manager can close the poll')
        self.assertFalse(poll.is_closed)

        # 6. /discuss/poll/close by author
        self.authenticate(self.poll_user.login, 'test_poll_user')
        auth_close = self.make_jsonrpc_request('/discuss/poll/close', {
            'poll_id': poll_id,
        })
        self.assertTrue(auth_close.get('success'))
        self.assertTrue(poll.is_closed)

        # Voting on closed poll returns error
        closed_vote_res = self.make_jsonrpc_request('/discuss/poll/vote', {
            'poll_id': poll_id,
            'option_ids': [opt_aws.id],
        })
        self.assertIn('error', closed_vote_res)
        self.assertEqual(closed_vote_res['error'], 'Poll is closed')

        # Reopen and test remove_votes endpoint
        poll.action_reopen()
        remove_res = self.make_jsonrpc_request('/discuss/poll/remove_votes', {
            'poll_id': poll_id,
        })
        self.assertEqual(remove_res['total_votes'], 0)
        self.assertEqual(remove_res['user_votes'], [])
