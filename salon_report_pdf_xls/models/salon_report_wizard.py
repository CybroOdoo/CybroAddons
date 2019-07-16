# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2015-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Avinash Nk(<http://www.cybrosys.com>)
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


class SalonReportMenu(models.TransientModel):

    _name = 'wizard.salon.report'

    chair_select = fields.Many2many('salon.chair', string="Chair")
    user_select = fields.Many2many('res.users', string="User")
    stage_select = fields.Many2many('salon.stages', string="Stage")

    @api.multi
    def print_salon_report_pdf(self):
        record = self.env['salon.order'].search([])
        return self.env['report'].get_action(record, "salon_report_pdf_xls.salon_report_pdf_details")

    @api.multi
    def print_salon_report_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'salon.order'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return {'type': 'ir.actions.report.xml',
                'report_name': 'salon_report_pdf_xls.salon_report_xls.xlsx',
                'datas': datas,
                'name': 'Salon Report',
                }