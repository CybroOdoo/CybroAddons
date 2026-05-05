# -*- coding: utf-8 -*-

from odoo.tests import common
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger

class TestPollVote(common.TransactionCase):

    def setUp(self):
        super(TestPollVote, self).setUp()
        self.partner_1 = self.env['res.partner'].create({'name': 'Voter 1'})
        self.partner_2 = self.env['res.partner'].create({'name': 'Voter 2'})

        self.poll_single = self.env['discuss.poll'].create({
            'question': 'Single Choice?',
            'is_multiple_choice': False,
            'option_ids': [
                (0, 0, {'name': 'Opt 1'}),
                (0, 0, {'name': 'Opt 2'})
            ]
        })
        self.poll_multi = self.env['discuss.poll'].create({
            'question': 'Multiple Choice?',
            'is_multiple_choice': True,
            'option_ids': [
                (0, 0, {'name': 'Opt 1'}),
                (0, 0, {'name': 'Opt 2'})
            ]
        })

    def test_01_single_choice_constraint(self):
        """Test that a user can only vote for one option in single-choice polls"""
        # First vote
        self.env['poll.vote'].create({
            'poll_id': self.poll_single.id,
            'option_id': self.poll_single.option_ids[0].id,
            'voter_id': self.partner_1.id
        })
        
        # Second vote should fail
        with self.assertRaises(ValidationError):
            self.env['poll.vote'].create({
                'poll_id': self.poll_single.id,
                'option_id': self.poll_single.option_ids[1].id,
                'voter_id': self.partner_1.id
            })

    def test_02_multiple_choice_allowed(self):
        """Test that a user can vote for multiple options in multiple-choice polls"""
        # First vote
        self.env['poll.vote'].create({
            'poll_id': self.poll_multi.id,
            'option_id': self.poll_multi.option_ids[0].id,
            'voter_id': self.partner_1.id
        })
        
        # Second vote should succeed
        self.env['poll.vote'].create({
            'poll_id': self.poll_multi.id,
            'option_id': self.poll_multi.option_ids[1].id,
            'voter_id': self.partner_1.id
        })
        
        self.poll_multi._compute_total_votes()
        self.assertEqual(self.poll_multi.total_votes, 1, "Total unique voters should be 1")

    @mute_logger('odoo.sql_db')
    def test_03_unique_vote_constraint(self):
        """Test SQL constraint: cannot vote for the same option twice"""
        self.env['poll.vote'].create({
            'poll_id': self.poll_single.id,
            'option_id': self.poll_single.option_ids[0].id,
            'voter_id': self.partner_1.id
        })
        
        with self.assertRaises(Exception): # SQL integrity error
            self.env['poll.vote'].create({
                'poll_id': self.poll_single.id,
                'option_id': self.poll_single.option_ids[0].id,
                'voter_id': self.partner_1.id
            })

    def test_04_closed_poll_constraint(self):
        """Test that users cannot vote in a closed poll"""
        self.poll_single.action_close()
        
        with self.assertRaises(ValidationError):
            self.env['poll.vote'].create({
                'poll_id': self.poll_single.id,
                'option_id': self.poll_single.option_ids[0].id,
                'voter_id': self.partner_1.id
            })
