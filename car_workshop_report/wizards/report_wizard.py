# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
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
from openerp import models, fields


class SaleReportWizard (models.Model):
    _name = "workshop.report"

    filter_partner = fields.Boolean('Enable Partner Filter')
    filter = fields.Selection([('filter_date', 'Date'), ], "Filter by")
    date_from = fields.Date("Start Date")
    date_to = fields.Date("End Date")
    filter_user = fields.Boolean("Enable Sales Person Filter")
    filter_vehicle = fields.Boolean("Filter By Vehicle")
    sales_person = fields.Many2many('res.users', string='Sales Person')
    partner_name = fields.Many2many('res.partner', 'multiple_partners', 'partner_names', string='Partner Name')
    vehicles = fields.Many2many('fleet.vehicle', string='Vehicle Name',)
    stage_id = fields.Many2one('worksheet.stages', string='Select State')

    def check_report(self, cr, uid, ids, context):
        data = self.read(cr, uid, ids, ['partner_name', 'filter_partner', 'filter_user',
                                        'filter', 'date_from', 'sales_person',
                                        'date_to', 'filter_vehicle', 'vehicles', 'stage_id'], context=context)[0]

        return {'type': 'ir.actions.report.xml',
                'report_name': 'workshop_report',
                'datas': data}

    def print_pdf(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, ['partner_name', 'filter_partner', 'filter_user',
                                        'filter', 'date_from', 'sales_person',
                                        'date_to', 'filter_vehicle', 'vehicles', 'stage_id'], context=context)[0]
        datas = {
            'ids': context.get('active_ids', []),
            'model': 'workshop.report',
            'form': data
        }
        datas['form']['active_ids'] = context.get('active_ids', False)
        return self.pool['report'].get_action(cr, uid, [], 'car_workshop_report.workshop_pdf', data=data,
                                              context=context)
