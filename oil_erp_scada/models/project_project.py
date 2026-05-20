# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models

class Project(models.Model):
    """
    Extends 'project.project' to handle SCADA-specific storage tank initialization.
    This logic is moved here to keep 'oil_erp_project' decoupled from SCADA.
    """
    _inherit = 'project.project'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides create to 'upgrade' the storage location of new Oil & Gas projects
        to be marked as Storage Tanks (ATG nodes).
        """
        projects = super().create(vals_list)
        for project in projects:
            if project.is_oil_gas_project and project.storage_location_id:
                # Update the linked storage location with SCADA tank flags
                project.storage_location_id.write({
                    'is_storage_tank': True,
                })
        return projects
