# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ATHUL RAJ B S (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
###############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MeetingChecklist(models.Model):
    """Meeting checklist model."""
    _name = 'meeting.checklist'
    _description = 'Meeting Checklist'
    _inherit = 'mail.thread'

    name = fields.Char(string="Name", required=True, help="Name of checklist.",
                       tracking=1)
    description = fields.Char(string="Description",
                              help="Description for checklist.")

    _sql_constraints = [
        ('checklist_name_unique', 'unique(name)', 'Checklist name must be unique!')
    ]

    @api.constrains('name')
    def _check_unique_name(self):
        """Check if the checklist name is unique."""
        for record in self:
            if self.search_count([('name', '=', record.name)]) > 1:
                raise ValidationError(_("Checklist name must be unique!"))
