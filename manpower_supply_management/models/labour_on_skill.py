# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###########################################################################
from odoo import fields, models


class LabourOnSkill(models.Model):
    """
    Labour On Skill

    This model represents the skill-wise labour requirements linked to a
    labour supply request. It allows defining how many workers are needed
    for a specific skill within a given date range.
    """

    _name = "labour.on.skill"
    _description = "Labour Requirement Based on Skill"
    _rec_name = "skill_id"

    skill_id = fields.Many2one(
        'skill.details',
        string="Required Skill",
        required=True,
        help="Select the skill or specialization required for the labour."
    )

    number_of_labour_required = fields.Integer(
        string="Number of Labours Required",
        help="Specify the total number of labourers required for the "
             "selected skill."
    )

    labour_supply_id = fields.Many2one(
        'labour.supply',
        string="Labour Supply",
        help="Reference to the labour supply request to which this skill "
             "requirement is linked."
    )

    from_date = fields.Date(
        string="From Date",
        required=True,
        help="Start date from which the labour is required for the "
             "selected skill."
    )

    to_date = fields.Date(
        string="To Date",
        required=True,
        help="End date until which the labour is required for the "
             "selected skill."
    )
