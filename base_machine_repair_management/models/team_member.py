# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
#############################################################################
from odoo import api, fields, models


class TeamMember(models.Model):
    """This is used for the team members of repair team"""
    _name = 'team.member'
    _description = 'Team Member'
    _rec_name = 'member_id'

    @api.onchange('member_id','inverse_id')
    def _onchange_member_id(self):
        """ On change of 'member_id' or 'inverse_id', links all member_ids from records
    with the same inverse_id to the current record."""
        for rec in self:
            if rec.inverse_id.ids:
             member_ids = self.search([('inverse_id','=',rec.inverse_id.ids[0])]).member_id
            else:
                member_ids = []
            for member_id in member_ids:
                rec.member_ids = [fields.Command.link(member_id.id)]

    inverse_id = fields.Many2one('repair.team', string="Repair Team",
                                 help="The repair team associated with this member.")
    member_id = fields.Many2one('hr.employee', string="Member",
                                help="The employee who is a member of the repair team.",
                                domain="[('id', 'not in', member_ids)]",
                                required=True)
    member_ids = fields.Many2many('hr.employee',help="To store values for member_id")
    login = fields.Char(related='member_id.work_email', string="Login",
                        help="The work email used as the login credential for the repair team member.")
