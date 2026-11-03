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
from odoo import fields, models


class SkillDetails(models.Model):
    """
    Skill Details

    This model defines the skills or specializations that can be assigned
    to workers and used in labour supply contracts. Skills are maintained
    company-wise to support multi-company environments.
    """

    _name = "skill.details"
    _description = "Worker Skill"

    name = fields.Char(
        string="Skill Name",
        required=True,
        help="Name of the skill or specialization, such as Electrician, "
             "Plumber, or Carpenter."
    )

    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        help="Company to which this skill belongs. This ensures skills "
             "are managed separately for each company."
    )

