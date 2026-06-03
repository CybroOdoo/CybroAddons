# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
################################################################################
from odoo import api, models


class VeterinaryManagementReport(models.AbstractModel):
    """
    Abstract model for generating veterinary reports.

    This class inherits from `models.AbstractModel` to provide a custom report
    for the veterinary management module. It defines the report template and
    provides the values necessary for generating the report.

    Attributes:
        _name (str): Internal name for the report model.
        _description (str): Short description of the report model.
    """
    _name = "report.veterinary_management.veterinary_report_template"
    _description = "Veterinary Report"

    @api.model
    def _get_report_values(self, data=None):
        """
        Get values for the veterinary report.
        This method is called when generating the report. It returns a dictionary
        containing the data to be displayed in the report.

        Args:
            docids (list): List of IDs for the records to include in the report.
            data (dict, optional): Additional data passed to the report.

        Returns:
            dict: A dictionary with the data needed for the report.
        """
        return {
            'data': data
        }
