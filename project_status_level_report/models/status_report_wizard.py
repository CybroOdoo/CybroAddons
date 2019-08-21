# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models, fields, api
from odoo.exceptions import except_orm


class ProjectExtended(models.Model):
    _inherit = 'project.project'

    planned_amount = fields.Float('Initially Planned Amount', help='Estimated cost to do the task.')


class StatusReportWizard(models.Model):
    _name = 'project.status_report'

    date_from = fields.Datetime('Start Date')
    date_to = fields.Datetime('End Date')

    @api.multi
    def print_report_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'project.project'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if len(datas['ids']) > 1:
            raise except_orm('Warning', 'Selection of multiple record is not allowed')
        else:
            return {'type': 'ir.actions.report.xml',
                    'report_name': 'project_status_level_report',
                    'datas': datas,
                    }
