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


class DiscussPoll(models.Model):
    """Model representing a poll created inside Discuss channels"""
    _name = 'discuss.poll'
    _description = 'Discuss Poll'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'question'

    question = fields.Char(string='Question', required=True)
    option_ids = fields.One2many('poll.option', 'poll_id', string='Options')
    vote_ids = fields.One2many('poll.vote', 'poll_id', string='Votes')
    message_id = fields.Many2one('mail.message', string='Message', ondelete='cascade' ,help="Related chatter message where this poll is posted")
    author_id = fields.Many2one('res.partner', string='Author', required=True,
                                default=lambda self: self.env.user.partner_id)
    is_multiple_choice = fields.Boolean(string='Multiple Choice', default=False)
    is_closed = fields.Boolean(string='Closed', default=False)
    total_votes = fields.Integer(string='Total Votes', compute='_compute_total_votes', store=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                default=lambda self: self.env.company,
                                help="Poll belongs to this company")


    @api.depends('vote_ids.voter_id')
    def _compute_total_votes(self):
        """
        Compute total unique voters for the poll.

        Ensures that multiple votes from the same user (in
        multiple-choice polls) are counted only once.
        """
        for poll in self:
            poll.total_votes = len(poll.vote_ids.mapped('voter_id'))

    @api.constrains('option_ids')
    def _check_minimum_options(self):
        """
        Ensure that a poll contains at least two options.
        """
        for poll in self:
            if len(poll.option_ids) < 2:
                raise ValidationError(_('A poll must have at least 2 options.'))

    def get_results(self):
        """Get poll results with vote counts and percentages"""
        self.ensure_one()
        current_user_votes = self.vote_ids.filtered(
            lambda v: v.voter_id == self.env.user.partner_id
        ).mapped('option_id').ids

        results = []
        for option in self.option_ids:
            vote_count = len(option.vote_ids)
            percentage = (vote_count / self.total_votes * 100) if self.total_votes > 0 else 0

            results.append({
                'id': option.id,
                'name': option.name,
                'sequence': option.sequence,
                'vote_count': vote_count,
                'percentage': round(percentage, 1),
            })

        return {
            'id': self.id,
            'question': self.question,
            'is_multiple_choice': self.is_multiple_choice,
            'is_closed': self.is_closed,
            'total_votes': self.total_votes,
            'options': sorted(results, key=lambda x: x['sequence']),
            'user_votes': current_user_votes,
            'is_author': self.author_id == self.env.user.partner_id,
        }

    def action_close(self):
        """Close the poll to prevent further voting"""
        self.ensure_one()
        self.is_closed = True

    def action_reopen(self):
        """Reopen the poll to allow voting again"""
        self.ensure_one()
        self.is_closed = False

    @api.model
    def action_open_polls(self):
        """
            Open the poll list and form views.

            Displays all polls for managers, and only the user's own polls
            for regular users.

            :return: Dictionary defining the action window
            """
        domain = []
        if not self.env.user.has_group('odoo_poll.group_odoo_poll_manager'):
            domain.append(('author_id', '=', self.env.user.partner_id.id))

        return {
            'name': _('Polls'),
            'type': 'ir.actions.act_window',
            'res_model': 'discuss.poll',
            'view_mode': 'list,form',
            'domain': domain,
            'context': self.env.context,
            'target': 'current',
        }
