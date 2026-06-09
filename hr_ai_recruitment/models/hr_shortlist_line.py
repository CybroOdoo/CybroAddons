# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM (odoo@cybrosys.com)
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
#
################################################################################
from odoo import fields, models

class HrShortlistLine(models.Model):
    """
    Represents a single criterion in a shortlisting configuration.
    Each line defines a specific requirement or evaluation factor
    and its corresponding score used in the AI shortlisting process.
    """
    _name = 'hr.shortlist.line'
    _description = 'Shortlisting Configuration Line'

    name = fields.Char(
        string="Criterion Name",
        help="The name or description of the shortlisting criterion."
    )
    score = fields.Integer(
        string="Score",
        help="The weight or score assigned to this criterion for applicant evaluation."
    )
    hr_shortlist_id = fields.Many2one(
        'hr.shortlist',
        string="Shortlisting Configuration",
        help="The shortlisting configuration this criterion belongs to."
    )
