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
from openerp.report import report_sxw
from openerp.osv import osv
from openerp.http import request


class SalonReportParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):

        super(SalonReportParser, self).__init__(cr, uid, name, context=context)

        self.localcontext.update({
            'get_salon_order_model': self.get_filtered_order_model,
            'get_total': self.get_total_sum,
        })
        self.context = context

    def get_filtered_order_model(self):
        wizard_record = request.env['wizard.salon.report'].search([])[-1]
        chairs = wizard_record.chair_select
        stages = wizard_record.stage_select
        users = wizard_record.user_select
        chairs_selected = []
        user_selected = []
        stage_selected = []
        for records in chairs:
            chairs_selected.append(records.id)
        for records in stages:
            stage_selected.append(records.id)
        for records in users:
            user_selected.append(records.id)
        if len(stage_selected) == 0:
            if len(user_selected) == 0:
                if len(chairs_selected) == 0:
                    salon_orders = wizard_record.env['salon.order'].search([])
                else:
                    salon_orders = wizard_record.env['salon.order'].search([('chair_id', 'in', chairs_selected)])
            else:
                if len(chairs_selected) == 0:
                    salon_orders = wizard_record.env['salon.order'].search([('chair_user', 'in', user_selected)])
                else:
                    salon_orders = wizard_record.env['salon.order'].search([('chair_id', 'in', chairs_selected),
                                                                            ('chair_user', 'in', user_selected)])
        else:
            if len(user_selected) == 0:
                if len(chairs_selected) == 0:
                    salon_orders = wizard_record.env['salon.order'].search([('stage_id', 'in', stage_selected)])
                else:
                    salon_orders = wizard_record.env['salon.order'].search([('chair_id', 'in', chairs_selected),
                                                                            ('stage_id', 'in', stage_selected)])
            else:
                if len(chairs_selected) == 0:
                    salon_orders = wizard_record.env['salon.order'].search([('chair_user', 'in', user_selected),
                                                                            ('stage_id', 'in', stage_selected)])
                else:
                    salon_orders = wizard_record.env['salon.order'].search([('chair_id', 'in', chairs_selected),
                                                                            ('chair_user', 'in', user_selected),
                                                                            ('stage_id', 'in', stage_selected)])
        return salon_orders

    def get_total_sum(self, salon_orders):
        sum = 0.0
        for records in salon_orders:
            sum += records.price_subtotal
        return sum


class PrintReportProject(osv.AbstractModel):

    _name = 'report.salon_report_pdf_xls.salon_report_pdf_details'
    _inherit = 'report.abstract_report'
    _template = 'salon_report_pdf_xls.salon_report_pdf_details'
    _wrapped_report_class = SalonReportParser


