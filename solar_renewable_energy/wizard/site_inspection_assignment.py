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


class SiteInspectionAssignment(models.TransientModel):
    """Class for site inspection wizard"""
    _name = "site.inspection.assignment"
    _description = "Site Inspection Assignment"

    survey_team_id = fields.Many2one(
        'survey.team',
        string="Survey Team",
        help="Select the survey team assigned to this inspection.")
    survey_member_id = fields.Many2one(
        'survey.team.member',
        string="Survey Member",
        domain="[('survey_team_id', '=', survey_team_id)]",
        help="Select a member of the selected survey team.")
    date_of_inspection = fields.Date(
        string="Date of Inspection",
        help="Specify the date when the inspection is scheduled.")
    lead_id = fields.Many2one(
        'crm.lead',
        string="Lead",
        help="Associate this inspection with a specific lead.")
    service_type_id = fields.Many2one('service.type', string="Service Type",
                                      help="Select the type of service for the customer.")

    def action_create_site_inspection(self):
        """Function to create site inspection"""
        inspection = self.env['site.inspection'].create({
            'name': self.lead_id.name,
            'crm_lead_id': self.lead_id.id,
            'survey_team_id': self.survey_team_id.id,
            'survey_team_member_id': self.survey_member_id.id,
            'date_of_inspection': self.date_of_inspection
        })
        self.lead_id.site_inspection_id = inspection.id
