# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2015-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Sreejith P(<http://www.cybrosys.com>)
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


class POSReport(models.TransientModel):
    _name = 'pos.report'

    date = fields.Datetime(string="Date", required=True)
    date_to = fields.Datetime(string="To Date", required=True)
    select_company = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    point_of_sale = fields.Many2one('pos.config', string='Point Of Sale')
    sales_person = fields.Many2one('res.users', string='Sales Person')

    def print_sales_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        datas = {
            'ids': context.get('active_ids'),
            'model': 'pos.report',
            'form': data,
            'name': 'POS Report'
        }
        datas['form']['active_ids'] = context.get('active_ids', False)
        return self.pool['report'].get_action(cr, uid, [], 'pos_sale_reports.report_daily_pos_sales', data=datas,
                                              context=context)
