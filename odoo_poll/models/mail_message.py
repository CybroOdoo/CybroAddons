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
from odoo import fields, models


class MailMessage(models.Model):
    """
       Extension of the mail.message model to integrate poll functionality.

       This model links Discuss polls with chatter messages, allowing polls
       to be embedded and displayed within the messaging system. Each message
       can optionally reference a poll, enabling users to interact with polls
       directly from the chatter interface.
       """
    _inherit = 'mail.message'

    poll_id = fields.Many2one('discuss.poll', string='Poll', ondelete='cascade')
