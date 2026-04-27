# -*- coding: utf-8 -*-
################################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#   This program is free software: you can modify
#   it under the terms of the GNU Affero General Public License (AGPL) as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DiscussPollVote(models.Model):
    """Model to store individual votes for a discuss poll"""
    _name = 'poll.vote'
    _description = 'Poll Vote'

    poll_id = fields.Many2one('discuss.poll', string='Poll', required=True, ondelete='cascade')
    option_id = fields.Many2one('poll.option', string='Option', required=True, ondelete='cascade')
    voter_id = fields.Many2one('res.partner', string='Voter', required=True,
                               default=lambda self: self.env.user.partner_id)

    _sql_constraints = [
        ('unique_vote', 'UNIQUE(poll_id, option_id, voter_id)',
         'You cannot vote for the same option twice!')
    ]

    @api.constrains('poll_id', 'voter_id')
    def _check_single_choice(self):
        """
        Ensure that users can only vote for one option
        the poll is configured as single-choice.
        """
        for vote in self:
            if not vote.poll_id.is_multiple_choice:
                existing_votes = self.search([
                    ('poll_id', '=', vote.poll_id.id),
                    ('voter_id', '=', vote.voter_id.id),
                    ('id', '!=', vote.id)
                ])
                if existing_votes:
                    raise ValidationError(_('You can only vote for one option in this poll.'))

    @api.constrains('poll_id')
    def _check_poll_closed(self):
        """Prevent voting if the poll is already closed"""
        for vote in self:
            if vote.poll_id.is_closed:
                raise ValidationError(_('This poll is closed.'))
