# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R(<https://www.cybrosys.com>)
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
###########################################################################
from odoo import api, models


class LabourSupplyPrint(models.AbstractModel):
    """ Class to print form view of contract"""

    _name = 'report.manpower_supply_management.form_print_labour_supply'
    _description = "Report for labour supply"

    @api.model
    def _get_report_values(self, docids, data=None):
        """ Function to print form view"""
        labour_supply = self.env['labour.supply'].browse(docids)
        return {
            'docs_ids': docids,
            'labour_supply': labour_supply
        }
