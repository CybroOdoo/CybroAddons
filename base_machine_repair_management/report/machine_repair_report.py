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
from odoo import fields, models


class MachineRepairReport(models.AbstractModel):
    """This is used to return the report data"""
    _name = 'report.base_machine_repair_management.machine_repair_report'
    _description = 'Report for machine repair management'

    def _get_report_values(self, docids, data=None):
        """This function is used to get the report data"""
        data = data or {}
        domain = []

        if data.get('from_date') and data.get('to_date'):
            domain.append(('repair_req_date', '>=', data['from_date']))
            domain.append(('repair_req_date', '<=', data['to_date']))
        elif data.get('from_date') and not data.get('to_date'):
            domain.append(('repair_req_date', '>=', data['from_date']))
        elif data.get('to_date') and not data.get('from_date'):
            domain.append(('repair_req_date', '<=', data['to_date']))

        if data.get('company_id'):
            domain.append(('company_id', '=', data['company_id']))
        if docids:
            repairs = self.env['machine.repair'].browse(docids)
        else:
            repairs = self.env['machine.repair'].search(domain)

        return {
            'date': fields.Date.today(),
            'doc_ids': repairs.ids,
            'doc_model': 'machine.repair',
            'repair_requests': repairs,
            'company': self.env.company,
            'data': data,
        }