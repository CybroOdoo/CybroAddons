# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jesni Banu(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
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
import time
from odoo.osv import osv
from odoo.report import report_sxw
from odoo.http import request


class AnalyticAccountBudgetReport(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(AnalyticAccountBudgetReport, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'funct': self.funct,
            'funct_total': self.funct_total,
            'time': time,
        })
        self.context = context

    def funct(self, object, form, ids=None, done=None, level=1):
        if ids is None:
            ids = {}
        if not ids:
            ids = self.ids
        if not done:
            done = {}

        global tot
        tot = {
            'theo': 0.00,
            'pln': 0.00,
            'prac': 0.00,
            'perc': 0.00
        }
        result = []
        accounts = request.env['account.analytic.account'].browse(object.id)
        c_b_lines_obj = request.env['crossovered.budget.lines']
        obj_c_budget = request.env['crossovered.budget']

        for account_id in accounts:
            res = {}
            b_line_ids = []
            for line in account_id.crossovered_budget_line:
                b_line_ids.append(line.id)
            if not b_line_ids:
                return []
            d_from = form['date_from']
            d_to = form['date_to']
            self.cr.execute('SELECT DISTINCT(crossovered_budget_id) FROM '
                            'crossovered_budget_lines WHERE id =ANY(%s)', (b_line_ids,))
            budget_ids = self.cr.fetchall()

            context = {'wizard_date_from': d_from, 'wizard_date_to': d_to}
            for i in range(0, len(budget_ids)):
                budget_name = obj_c_budget.browse([budget_ids[i][0]])
                res = {
                     'b_id': '-1',
                     'a_id': '-1',
                     'name': budget_name[0].name,
                     'status': 1,
                     'theo': 0.00,
                     'pln': 0.00,
                     'prac': 0.00,
                     'perc': 0.00
                }
                result.append(res)

                line_ids = c_b_lines_obj.search([('id', 'in', b_line_ids),
                                                 ('crossovered_budget_id', '=', budget_ids[i][0])])
                line_id = line_ids
                tot_theo = tot_pln = tot_prac = tot_perc = 0

                done_budget = []
                for line in line_id:
                    if line.id in b_line_ids:
                        theo = pract = 0.00
                        theo = line.theoritical_amount
                        pract = line.practical_amount
                        if line.general_budget_id.id in done_budget:
                            for record in result:
                                if record['b_id'] == line.general_budget_id.id and \
                                                record['a_id'] == line.analytic_account_id.id:
                                    record['theo'] += theo
                                    record['pln'] += line.planned_amount
                                    record['prac'] += pract
                                    record['perc'] += line.percentage
                                    tot_theo += theo
                                    tot_pln += line.planned_amount
                                    tot_prac += pract
                                    tot_perc += line.percentage
                        else:
                            res1 = {
                                 'b_id': line.general_budget_id.id,
                                 'a_id': line.analytic_account_id.id,
                                 'name': line.general_budget_id.name,
                                 'status': 2,
                                 'theo': theo,
                                 'pln': line.planned_amount,
                                 'prac': pract,
                                 'perc': line.percentage
                            }
                            tot_theo += theo
                            tot_pln += line.planned_amount
                            tot_prac += pract
                            tot_perc += line.percentage
                            result.append(res1)
                            done_budget.append(line.general_budget_id.id)
                    else:
                        if line.general_budget_id.id in done_budget:
                            continue
                        else:
                            res1 = {
                                    'b_id': line.general_budget_id.id,
                                    'a_id': line.analytic_account_id.id,
                                    'name': line.general_budget_id.name,
                                    'status': 2,
                                    'theo': 0.00,
                                    'pln': 0.00,
                                    'prac': 0.00,
                                    'perc': 0.00
                            }
                            result.append(res1)
                            done_budget.append(line.general_budget_id.id)
                if tot_theo == 0.00:
                    tot_perc = 0.00
                else:
                    tot_perc = float(tot_prac / tot_theo) * 100

                result[-(len(done_budget) + 1)]['theo'] = tot_theo
                tot['theo'] += tot_theo
                result[-(len(done_budget) + 1)]['pln'] = tot_pln
                tot['pln'] += tot_pln
                result[-(len(done_budget) + 1)]['prac'] = tot_prac
                tot['prac'] += tot_prac
                result[-(len(done_budget) + 1)]['perc'] = tot_perc
            if tot['theo'] == 0.00:
                tot['perc'] = 0.00
            else:
                tot['perc'] = float(tot['prac'] / tot['theo']) * 100
        return result

    def funct_total(self, form):
        result = []
        res = {
             'tot_theo': tot['theo'],
             'tot_pln': tot['pln'],
             'tot_prac': tot['prac'],
             'tot_perc': tot['perc']
        }
        result.append(res)
        return result


class ReportAnalyticAccountBudget(osv.AbstractModel):
    _name = 'report.account_budget_report.report_analytic_account_budget'
    _inherit = 'report.abstract_report'
    _template = 'account_budget_report.report_analytic_account_budget'
    _wrapped_report_class = AnalyticAccountBudgetReport
