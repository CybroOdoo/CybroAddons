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
from openerp.report import report_sxw
from openerp.osv import osv
from dateutil import parser
import datetime
import pytz
from datetime import datetime
from pytz import timezone
from openerp import SUPERUSER_ID
fmt1 = "%Y-%m-%d"


class POSReportParser(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(POSReportParser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'get_sale_details': self.get_sale_details,
            'get_date': self.get_date,
            'get_change_date': self.get_change_date,

        })
        self.context = context

    def get_date(self):
        now_utc = datetime.now(timezone('UTC'))
        user_list = self.pool.get('res.users').search(self.cr, self.uid,
                                                      [('id', '=', SUPERUSER_ID)])
        obj1 = self.pool.get('res.users').browse(self.cr, self.uid, user_list, context=None)
        tz = pytz.timezone(obj1.partner_id.tz)
        now_pacific = now_utc.astimezone(timezone(str(tz)))
        current_date = now_pacific.strftime(fmt1)
        return current_date

    def get_change_date(self, data):
        my_date = parser.parse(data['form']['date'])
        proper_date_string = my_date.strftime('%d-%m-%Y')
        return proper_date_string

    def get_sale_details(self, data):
        lines = []
        if data['form']['sales_person'] and data['form']['point_of_sale']:
            pos_orders = self.pool.get('pos.order').search(self.cr, self.uid,
                                                           [('date_order', '>=', data['form']['date']),
                                                            ('date_order', '<=', data['form']['date_to']),
                                                            ('user_id', '=', data['form']['sales_person'][0]),
                                                            ('session_id.config_id', '=', data['form']['point_of_sale'][0])])
        elif data['form']['point_of_sale']:
            pos_orders = self.pool.get('pos.order').search(self.cr, self.uid,
                                                           [('date_order', '>=', data['form']['date']),
                                                            ('date_order', '<=', data['form']['date_to']),
                                                            ('session_id.config_id', '=', data['form']['point_of_sale'][0])])
        elif data['form']['sales_person']:
            pos_orders = self.pool.get('pos.order').search(self.cr, self.uid,
                                                           [('date_order', '>=', data['form']['date']),
                                                            ('date_order', '<=', data['form']['date_to']),
                                                            ('user_id', '=', data['form']['sales_person'][0])])
        else:
            pos_orders = self.pool.get('pos.order').search(self.cr, self.uid,
                                                           [('date_order', '>=', data['form']['date']),
                                                            ('date_order', '<=', data['form']['date_to'])])
        for order in pos_orders:
            obj1 = self.pool.get('pos.order').browse(self.cr, self.uid, order, context=None)
            if data['form']['select_company'][0] == 1:
                order = obj1.name
                if obj1.partner_id.name:
                    partner = obj1.partner_id.name
                else:
                    partner = ""
                price = obj1.amount_total
                bank_amount = 0
                cash_amount = 0
                for statements in obj1.statement_ids:
                    if statements.journal_id.name == "Debt":
                        debit = debit + statements.amount
                        continue
                    if statements.journal_id.type == "bank":
                        if statements.amount > price:
                            bank_amount += price
                        elif statements.amount > 0:
                            bank_amount += statements.amount
                        else:
                            pass
                    if statements.journal_id.type == "cash":
                        if statements.amount > price:
                            cash_amount += price
                        elif statements.amount > 0:
                            cash_amount += statements.amount
                        else:
                            pass

                vals = {
                    'order': order,
                    'partner': partner,
                    'price': price,
                    'cash': cash_amount,
                    'bank': bank_amount,
                }
                lines.append(vals)
            elif obj1.company_id.id == data['form']['select_company'][0]:
                order = obj1.name
                if obj1.partner_id.name:
                    partner = obj1.partner_id.name
                else:
                    partner = ""
                price = obj1.amount_total
                bank_amount = 0
                cash_amount = 0
                for statements in obj1.statement_ids:
                    if statements.journal_id.type == "bank":
                        if statements.amount > price:
                            bank_amount += price
                        elif statements.amount > 0:
                            bank_amount += statements.amount
                        else:
                            pass
                    if statements.journal_id.type == "cash":
                        if statements.amount > price:
                            cash_amount += price
                        elif statements.amount > 0:
                            cash_amount += statements.amount
                        else:
                            pass

                vals = {
                       'order': order,
                       'partner': partner,
                       'price': price,
                       'cash': cash_amount,
                       'bank': bank_amount,
                       }
                lines.append(vals)
        return lines


class PrintReport(osv.AbstractModel):
    _name = 'report.pos_sale_reports.report_daily_pos_sales'
    _inherit = 'report.abstract_report'
    _template = 'pos_sale_reports.report_daily_pos_sales'
    _wrapped_report_class = POSReportParser
