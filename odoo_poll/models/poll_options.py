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
from odoo import api, fields, models


class DiscussPollOption(models.Model):
    """Model representing individual options for a poll"""

    _name = "poll.option"
    _description = "Poll Option"
    _order = "sequence, id"

    poll_id = fields.Many2one("discuss.poll", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    vote_count = fields.Integer(string="Vote Count", compute="_compute_vote_count", store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    vote_ids = fields.One2many('poll.vote', 'option_id', string="Votes")

    @api.depends('vote_ids')
    def _compute_vote_count(self):
        for option in self:
            option.vote_count = len(option.vote_ids)

