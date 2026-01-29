# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
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
#############################################################################
from odoo import models


class CleaningManagementWebsite(models.Model):
    """Creating new model to search teams for website """
    _name = "cleaning.management.website"
    _description = "Cleaning Management Website"

    def get_team_details(self):
        """Search for teams from the cleaning_team model and
        pass all data to the frontend."""
        teams = self.env["cleaning.team"].search([])
        return {'team_list': [
            {'id': team.id, 'name': team.name, 'duty': team.duty_type}
            for team in teams],
                'duty': [{'id': duty.id, 'team_id': duty.team_id.id,
                          'team_name': duty.team_id.name,
                          'duty': duty.cleaning_time,
                          'date': duty.cleaning_date}
                         for duty in self.env["cleaning.team.duty"].search([])]}
