"""Machine repair management"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
from odoo import models, fields


class MachineRepairReports(models.AbstractModel):
    """This is used to return the report data"""
    _name = 'report.base_machine_repair_management.machine_repair_report'
    _description = 'Report for machine repair management'

    def _get_report_values(self, docids, data=None):
        """This function is used to get the report data"""
        if data['from_date'] and data['to_date']:
            vals = self.env['machine.repair'].search(
                [('repir_req_date', '>=', data['from_date']),
                 ('repir_req_date', '<=', data['to_date'])])
        else:
            vals = self.env['machine.repair'].search([])
        return {
            'date': fields.Date.today(),
            'doc_ids': docids,
            'doc_model': 'machine.repair',
            'repair_requests': vals,
            'company': self.env.company,
            'data': data,
        }
