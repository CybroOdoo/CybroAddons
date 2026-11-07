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
from odoo import api, models


class ScrapManagementPrint(models.AbstractModel):
    """ This class defines a new model to print scrap management report"""
    _name = 'report.company_scrap_management.report_scrap_management'
    _description = "Scrap Management Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        """Function to print the report"""
        scrap_management = self.env['scrap.management'].browse(docids)
        return {
            'scrap_management': scrap_management
        }
