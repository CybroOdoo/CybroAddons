# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nandakishore M (odoo@cybrosys.info)
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
from random import randint
from odoo import fields, models


class VolunteerSkills(models.Model):
    """This class represents the skills that a volunteer can possess.

     Methods: _default_color(): Set the Color based on VolunteerSkills
     inside the tree view"""
    _name = "volunteer.skill"
    _description = "Volunteer Skill"
    _rec_name = 'volunteer_skill'

    def _default_color(self):
        """Set the Color based on VolunteerSkills inside the tree view"""
        return randint(1, 11)

    volunteer_skill = fields.Char(String='Name', help='The name of the '
                                                      'volunteer skill',
                                  required=True)
    volunteer_skill_code = fields.Char(String='code', help='The code of the '
                                                           'volunteer skill',
                                       required=True,)
    color = fields.Integer(string='Color', default=_default_color,
                           help='The color code of the volunteer skill')

    description = fields.Html(string='Description', translate=True,
                              help='A description of the volunteer skill')
