# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Nilmar Shereef(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _


class ProjectReportButton(models.TransientModel):
    _name = 'wizard.project.report'

    task_select = fields.Boolean(string="Task", default=True)
    issue_select = fields.Boolean(string="Issue", default=True)
    partner_select = fields.Many2many('res.users', string='Assigned to')
    stage_select = fields.Many2many('project.task.type', string="Stage")

    @api.multi
    def print_project_report_pdf(self):

        active_record = self._context['active_id']
        record = self.env['project.project'].browse(active_record)
        return self.env['report'].get_action(record, "project_report_pdf.project_report_transition")

    @api.multi
    def print_project_report_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'project.project'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return {'type': 'ir.actions.report.xml',
                'report_name': 'project_report_pdf.project_report_xls.xlsx',
                'datas': datas,
                'name': 'Project Report'
                }
