# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amrithesh K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models

class InstallationTeam(models.Model):
    """Class for solar project installation team"""
    _name = "installation.team"
    _description = "Installation Team"

    name = fields.Char(string="Title", required=True, help="Name of the installation team")
    project_manager_id = fields.Many2one('res.users', string="Project Manager", help="Manager of the installation team")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, help="Company associated with this team")
    team_member_ids = fields.One2many('installation.team.member', 'installation_team_id', string="Team Members", help="Members of the installation team")