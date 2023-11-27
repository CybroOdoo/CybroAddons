# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class CleaningTeam(models.Model):
    """ Model for creating Cleaning team and assigns Cleaning requests to
    each team"""
    _name = "cleaning.team"
    _description = "Cleaning Team"

    name = fields.Char(string="Team Name", help="Name of the Team")
    team_head_id = fields.Many2one('res.users', string="Team Head",
                                   help="Choose the Team Head",
                                   domain=lambda self: [
                                       ('groups_id', 'in', self.env.ref(
                                           'hotel_management_odoo.'
                                           'cleaning_team_group_head').id)])
    member_ids = fields.Many2many('res.users', string="Member",
                                  domain=lambda self: [
                                      ('groups_id', 'in', self.env.ref(
                                          'hotel_management_odoo.'
                                          'cleaning_team_group_user').id)],
                                  help="Team Members")
