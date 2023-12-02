# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class CrmTeam(models.Model):
    """Inheriting CrmTeam class to set the Team Target and compute its value
        based on the CRM Team member assigned"""
    _inherit = 'crm.team'

    team_target = fields.Float(string="Team Target",
                               help="Automatically calculated value for every "
                                    "Sales Team based on the individual "
                                    "targets of the Salespersons")

    @api.model
    def default_get(self, fields):
        """Calculate the team target's value called from the onchange of
        sale_user_id or user_target fields in target form"""
        self.team_target = 0.0
        for record in self.env['target.achieve'].search([
                    ('team_id', '=', self.id)]):
            self.team_target = self.team_target + record.user_target
        return super(CrmTeam, self).default_get(fields)
