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
from odoo import fields, models


class MachineRepairReport(models.AbstractModel):
    """Provide the data for the machine repair report."""
    _name = 'report.base_machine_repair_management.machine_repair_report'
    _description = 'Report for machine repair management'

    def _get_report_values(self, docids, data=None):
        """Return the values used by the report template."""
        data = data or {}
        domain = []
        if data.get('from_date'):
            domain.append(('repair_req_date', '>=', data['from_date']))
        if data.get('to_date'):
            domain.append(('repair_req_date', '<=', data['to_date']))
        if not domain and docids:
            domain = [('id', 'in', docids)]
        vals = self.env['machine.repair'].search(domain)
        return {
            'date': fields.Date.today(),
            'doc_ids': docids,
            'doc_model': 'machine.repair',
            'repair_requests': vals,
            'company': self.env.company,
            'data': data,
        }
