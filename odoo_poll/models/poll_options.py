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
from odoo.exceptions import UserError

class DiscussPollOption(models.Model):
    """Model representing individual options for a poll"""

    _name = "poll.option"
    _description = "Poll Option"
    _order = "sequence, id"

    poll_id = fields.Many2one("discuss.poll", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    vote_count = fields.Integer(string='Vote Count', compute='_compute_vote_count', store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    vote_ids = fields.One2many('poll.vote', 'option_id', string="Votes")

    @api.depends('vote_ids')
    def _compute_vote_count(self):
        """Compute the number of votes for each option"""
        for option in self:
            option.vote_count = len(option.vote_ids)

    def unlink(self):
        """Prevent deletion of options that have already been voted on"""
        for option in self:
            if option.vote_count > 0:
                raise UserError(_("You cannot delete an option that already has votes ('%s').") % option.name)
        return super(DiscussPollOption, self).unlink()

