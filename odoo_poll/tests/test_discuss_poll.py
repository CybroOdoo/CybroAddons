# -*- coding: utf-8 -*-

from odoo.tests import common
from odoo.exceptions import ValidationError

class TestDiscussPoll(common.TransactionCase):

    def setUp(self):
        super(TestDiscussPoll, self).setUp()
        self.user_admin = self.env.ref('base.user_admin')
        self.partner_admin = self.user_admin.partner_id

    def test_01_poll_creation_and_constraints(self):
        """Test poll creation and minimum options constraint"""
        # Test minimum options constraint (less than 2)
        with self.assertRaises(ValidationError):
            self.env['discuss.poll'].create({
                'question': 'How are you?',
                'option_ids': [(0, 0, {'name': 'Good'})]
            })

        # Correct creation
        poll = self.env['discuss.poll'].create({
            'question': 'How are you?',
            'option_ids': [
                (0, 0, {'name': 'Good'}),
                (0, 0, {'name': 'Not Good'})
            ]
        })
        self.assertEqual(len(poll.option_ids), 2)
        self.assertEqual(poll.total_votes, 0)

    def test_02_poll_results_sum(self):
        """Test vote counting and get_results function"""
        poll = self.env['discuss.poll'].create({
            'question': 'Favorite Color?',
            'option_ids': [
                (0, 0, {'name': 'Red', 'sequence': 1}),
                (0, 0, {'name': 'Blue', 'sequence': 2})
            ]
        })
        option_red = poll.option_ids[0]
        option_blue = poll.option_ids[1]

        # Add a vote
        self.env['poll.vote'].create({
            'poll_id': poll.id,
            'option_id': option_red.id,
            'voter_id': self.partner_admin.id
        })
        
        poll._compute_total_votes()
        self.assertEqual(poll.total_votes, 1)

        results = poll.get_results()
        self.assertEqual(results['total_votes'], 1)
        self.assertEqual(results['options'][0]['vote_count'], 1)
        self.assertEqual(results['options'][0]['percentage'], 100.0)
        self.assertEqual(results['options'][1]['vote_count'], 0)
        self.assertEqual(results['options'][1]['percentage'], 0.0)

    def test_03_poll_state_management(self):
        """Test closing and reopening a poll"""
        poll = self.env['discuss.poll'].create({
            'question': 'Is this closed?',
            'option_ids': [
                (0, 0, {'name': 'Yes'}),
                (0, 0, {'name': 'No'})
            ]
        })
        self.assertFalse(poll.is_closed)
        
        poll.action_close()
        self.assertTrue(poll.is_closed)
        
        poll.action_reopen()
        self.assertFalse(poll.is_closed)
