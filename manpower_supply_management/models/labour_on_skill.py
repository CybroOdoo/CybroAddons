# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R(<https://www.cybrosys.com>)
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
    This model is used to create a table field in the main model
    for managing labor allocation based on skills.
           """

    _name = "labour.on.skill"
    _description = "Selection of labour on skill"
    _rec_name = "skill_id"

    skill_id = fields.Many2one('skill.details',
                               string="Skill required", required=True,
                               help="Field to choose skill")
    number_of_labour_required = fields.Integer(
        string="Number of labours required",
        help="Field to give number of labour required")
    labour_supply_id = fields.Many2one(
        'labour.supply',
        help="Many2one field to represent labour supply")
    from_date = fields.Date(string="From date", required=True,
                            help="Field to choose from date")
    to_date = fields.Date(string="To date", required=True,
                          help="Field to choose to date")
