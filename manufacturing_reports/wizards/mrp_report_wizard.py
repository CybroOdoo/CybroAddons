# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2014-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Cybrosys Technologies(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


class MrpReportWizard (models.Model):
    _name = "mrp.report"

    filter = fields.Boolean('Enable filter by date')
    date_from = fields.Date("Start Date")
    date_to = fields.Date("End Date")
    filter_user = fields.Boolean("Filter On Responsible")
    responsible = fields.Many2many('res.users', string='Responsible')
    product = fields.Many2many('product.product', string='Product')
    stage = fields.Selection([
        ('confirmed', 'Confirmed'),
        ('planned', 'Planned'),
        ('progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')], string="Filter State")

    def check_report(self, cr, uid, ids, context):
        data = self.read(cr, uid, ids, ['filter_user',
                                        'filter', 'date_from', 'responsible',
                                        'date_to', 'product', 'stage'], context=context)[0]
        return {'type': 'ir.actions.report.xml',
                'report_name': 'mrp_reports_xls',
                'datas': data}

    def print_pdf(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, ['filter_user',
                                        'filter', 'date_from', 'responsible',
                                        'date_to', 'product', 'stage'], context=context)[0]
        datas = {
            'ids': context.get('active_ids', []),
            'model': 'mrp.report',
            'form': data
        }
        datas['form']['active_ids'] = context.get('active_ids', False)
        return self.pool['report'].get_action(cr, uid, [], 'manufacturing_reports.mrp_pdf', data=data,
                                              context=context)
