# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models

class InformationArticleReading(models.Model):
    """Tracks per-user reading assignments for info articles.

    Each record represents a single user's obligation to read a specific article.
    When the user clicks 'Acknowledge', the state transitions from 'pending' to 'read'.
    """
    _name = 'info.hub.article.reading'
    _description = 'Information Article Reading'
    _order = 'create_date desc, id desc'

    article_id = fields.Many2one(
        comodel_name='info.hub.article',
        string='Article',
        domain="[('is_template', '=', False), ('is_article_item', '=', False)]",
        required=True,
        ondelete='cascade',
        index=True,
        help='The article assigned to be read.',
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        ondelete='cascade',
        index=True,
        help='The user assigned to read the article.',
    )
    state = fields.Selection(
        [('pending', 'Pending'), ('read', 'Read')],
        string='State',
        default='pending',
        required=True,
        index=True,
        help='Status of the reading assignment (Pending or Read).',
    )
    read_date = fields.Datetime(
        string='Read Date',
        readonly=True,
        help='Date and time when the user acknowledged reading the article.',
    )

    _user_article_unique = models.Constraint('UNIQUE(user_id, article_id)', 'A user can only have one reading assignment per article.')


    def action_acknowledge(self):
        """Mark this reading record as acknowledged by the assigned user.
        Sets the state to 'read' and records the current timestamp as the read date.
        """
        self.ensure_one()
        self.write({
            'state': 'read',
            'read_date': fields.Datetime.now(),
        })
        return True
