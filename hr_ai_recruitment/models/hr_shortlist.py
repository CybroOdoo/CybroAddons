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

class HRShortlistConfig(models.Model):
    """
    Configuration model for AI shortlisting criteria.
    Stores the configuration name and related criteria lines
    that define how applicants should be shortlisted.
    """
    _name = 'hr.shortlist'
    _description = 'Shortlisting Configuration'

    name = fields.Char(
        string="Configuration Name",
        required=True,
        help="A descriptive name for this shortlisting configuration, "
             "e.g., 'Sales Role AI Criteria - 2025'."
    )
    hr_shortlist_line_ids = fields.One2many(
        'hr.shortlist.line',
        'hr_shortlist_id',
        string="Shortlisting Criteria Lines",
        help="The set of criteria lines that define how applicants "
             "are evaluated and shortlisted for this configuration."
    )
