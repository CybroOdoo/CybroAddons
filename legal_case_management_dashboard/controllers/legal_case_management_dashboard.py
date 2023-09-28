"""Legal Case Management Dashboard"""
# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from datetime import date, timedelta
from odoo import fields, http
from odoo.http import request


class CaseDashboard(http.Controller):
    """Values for chart and dashboard when filter not applied"""

    @http.route('/case/dashboard', type='json', auth='user')
    def _get_case_dashboard_values(self):
        """Values for charts, graph and dashboard cards without filtering"""
        moves, inv, client, inv_list, lawyers = [], [], [], [], []
        data_list = [['Month', 'Income']]
        stage_count = [['Stage', 'Cases']]
        case_category = [['Category', 'Number']]
        lawyer_object = None
        draft_count, in_progress_count, invoiced_count, reject_count = 0, 0, 0, 0
        won_count, lost_count, cancel_count, inv_amt = 0, 0, 0, 0
        today_date = fields.Date.today()
        cases = request.env['case.registration'].search([])
        # getting last 1 year month range for bar chart
        for num in range(0, 13):
            month_sub = timedelta(days=num * 30)
            current_first_date = today_date.replace(day=5)
            range_date = current_first_date - month_sub
            first_day = range_date.replace(day=1)
            last_day = range_date.replace(day=1) + timedelta(days=32)
            last_day = last_day.replace(day=1) - timedelta(days=1)
            month_name = range_date.strftime("%b")
            monthly_invoice = 0
            for invoices in request.env['account.move'].search([]):
                if invoices.case_ref:
                    inv_date = invoices.invoice_date
                    if first_day < inv_date < last_day:
                        monthly_invoice += invoices.amount_total
            data_list.append([month_name, monthly_invoice])
        # Calculate count of case in different category's
        for category_id in request.env['case.category'].search([]):
            case_count = request.env['case.registration'].search_count(
                [('case_category_id', '=', category_id.id)])
            case_category.append([category_id.name, case_count])
        for case in cases:
            # lawyers.append(case.lawyer_id.id)
            for invoices in request.env['account.move'].search([]):
                if case.name == invoices.case_ref:
                    # add case name, amount invoiced into list then it look
                    # like [Case0001, 5500.5]
                    inv_list.append([case.name, invoices.amount_total])
            if case.state == 'draft':
                draft_count += 1
            if case.state == 'in_progress':
                in_progress_count += 1
            if case.state == 'invoiced':
                invoiced_count += 1
            if case.state == 'reject':
                reject_count += 1
            if case.state == 'won':
                won_count += 1
            if case.state == 'lost':
                lost_count += 1
            if case.state == 'cancel':
                cancel_count += 1
            client.append(case.client_id.id)
            for total_invoices in request.env['account.move'].search(
                    [('case_ref', '=', case.name)]):
                if total_invoices:
                    inv.append(total_invoices)
                    moves.append(total_invoices.id)
                inv_amt += total_invoices.amount_total
        case_dict = {}
        for case, amount in inv_list:
            if case in case_dict:
                case_dict[case] += amount  # add amount to existing case
            else:
                case_dict[case] = amount  # add new case to dictionary
        # Add all invoice amount to each case names and in to list
        total_inv_lis = [[case, amount] for case, amount in case_dict.items()]
        sorted_cases = sorted(total_inv_lis, key=lambda case: case[1],
                              reverse=True)
        top_10_cases = sorted_cases[:10]
        # appending count of each stages into stage_count
        stage_count.append(['Draft', draft_count])
        stage_count.append(['In Progress', in_progress_count])
        stage_count.append(['Invoiced', invoiced_count])
        stage_count.append(['Reject', reject_count])
        stage_count.append(['Won', won_count])
        stage_count.append(['Lost', lost_count])
        stage_count.append(['Cancel', cancel_count])
        evidence = request.env['legal.evidence'].search([])
        trial = request.env['legal.trial'].search([])
        lawyers = request.env['hr.employee'].search([]).filtered(
                        lambda employee: not employee.parent_id and
                                         employee.is_lawyer is True)
        # extract integer from lawyers list which contains false
        lawyer_list = list(filter(lambda x: x is not False, lawyers))
        #append['Case', 'Revenue']in to 0th index of list for pass to donut chart
        top_10_cases.insert(0, ['Case', 'Revenue'])
        user_id = request.env.uid
        login_user = request.env['res.users'].search(
            [('employee_id.user_id', '=', user_id)])
        if login_user.has_group('legal_case_management.lawyer_access'):
            if not login_user.has_group('legal_case_management.admin_access'):
                lawyer_object = login_user.employee_id
            else:
                lawyer_object = None
        return {'total_case': len(cases),
                'invoices': inv,
                'total_invoiced': round(inv_amt, 4),
                'lawyers': len(lawyer_list),
                'lawyer_ids': lawyer_list,
                'evidences': len(evidence),
                'trials': len(trial),
                'clients': len(list(set(client))),#remove duplicates from list
                'clients_in_case': client,
                'case_category': case_category,
                'data_list': data_list,
                'stage_count': stage_count,
                'invoice_list': total_inv_lis,
                'top_10_cases': top_10_cases,
                'user_id': user_id,
                'lawyer_object': lawyer_object,
                }

class AddLawyerSelectionFieldController(http.Controller):
    """Add lawyers as selection values in Dashboard"""

    @http.route('/selection/field/lawyer', type='json', auth='user',
                csrf=False)
    def add_lawyer_selection_field(self):
        """Adding lawyers to selection of filter"""
        return [{'name': lawyer.name,
                 'id': lawyer.id
                 } for lawyer in request.env['hr.employee'].search(
            [('is_lawyer', '=', True), ('parent_id', '=', False)])]

    def date_filter(self):
        """ Month filter for dashboard """
        today_date = fields.Date.today()
        first_day_of_month = date(today_date.year, today_date.month, 1)
        # subtract one day from the first day of the current month to get
        # the last day of the previous month
        last_day_of_last_month = first_day_of_month - timedelta(days=1)
        six_months_ago = today_date - timedelta(days=30 * 6)
        first_day_of_six_months_ago = date(six_months_ago.year,
                                           six_months_ago.month, 1)
        twelve_months_ago = today_date - timedelta(days=30 * 12)
        first_day_of_twelve_months_ago = date(twelve_months_ago.year,
                                              twelve_months_ago.month, 1)
        return {
            'first_day_of_last_month': date(last_day_of_last_month.year,
                                       last_day_of_last_month.month, 1),
            'last_day_of_last_month': last_day_of_last_month,
            'first_day_of_six_months_ago': first_day_of_six_months_ago,
            'first_day_of_twelve_months_ago': first_day_of_twelve_months_ago,
        }

    @http.route('/dashboard/filter', type='json', auth='user')
    def fetch_dashboard_filter_value(self, **kw):
        """Lawyer wise and stage wise filter"""
        trial_list, clients, case_list, evidence_list, lawyer_ids, inv_amt = [], \
            [], [], [], [], 0
        data = kw['data']
        if data['stage'] == 'null':
            stage_list = ['draft', 'in_progress', 'invoiced', 'won', 'lost',
                          'cancel']
        else:
            stage_list = [data['stage']]
        if data['lawyer'] == 'admin':
            lawyer_list = [lawyer.id for lawyer in
                           request.env['hr.employee'].search(
                               [('is_lawyer', '=', True),
                                ('parent_id', '=', False)])]
        else:
            lawyer_list = [int(data['lawyer'])]
            lawyer_list = [lawyer.id for lawyer in
                           request.env['hr.employee'].search(
                               [('id', 'in', lawyer_list)])]
        if data['month_wise'] != 'null':
            month_wise_list = [data['month_wise']]
            filter_start_date = None
            filter_end_date = self.date_filter()
            filter_end_date = filter_end_date['last_day_of_last_month']
            if month_wise_list[0] == 'last_month':
                filter_start_date = self.date_filter()
                filter_start_date = filter_start_date['first_day_of_last_month']
            elif month_wise_list[0] == 'last_6_months':
                filter_start_date = self.date_filter()
                filter_start_date = filter_start_date[
                    'first_day_of_six_months_ago']
            elif month_wise_list[0] == 'last_12_months':
                filter_start_date = self.date_filter()
                filter_start_date = filter_start_date[
                    'first_day_of_twelve_months_ago']
            if data['lawyer'] == 'admin':
                registration_ids = request.env['case.registration'].search(
                    [('start_date', '>=', filter_start_date),
                     ('start_date', '<=', filter_end_date),
                     ('state', 'in', stage_list)])
            else:
                lawyer_list = data['lawyer']
                registration_ids = request.env['case.registration'].search(
                    [('start_date', '>=', filter_start_date),
                     ('start_date', '<=', filter_end_date),
                     ('state', 'in', stage_list),
                     ('lawyer_id.id', 'in', [lawyer_list])])
                lawyer_list = [lawyer.id for lawyer in
                               request.env['hr.employee'].search(
                                   [('id', '=', lawyer_list)])]
        else:
            if data['lawyer'] == 'admin':
                registration_ids = request.env['case.registration'].search(
                    [('state', 'in', stage_list)])
                lawyer_list = [lawyer.id for lawyer in
                               request.env['hr.employee'].search(
                                   [('is_lawyer', '=', True),
                                    ('parent_id', '=', False)])]
            else:
                registration_ids = request.env['case.registration'].search(
                    [('state', 'in', stage_list),
                     ('lawyer_id.id', 'in', lawyer_list)])
        for registration_id in registration_ids:
            lawyer_ids.append(registration_id.lawyer_id.id)
            case_list.append(registration_id.id)
            clients.append(request.env['res.partner'].browse(
                registration_id.client_id.id).id)
            inv_amt += sum(request.env['account.move'].search(
                [('case_ref', '=', registration_id.name)]).mapped(
                'amount_total'))
        trial_list = [trial.id for trial in request.env['legal.trial'].search(
            [('case_id.id', 'in', case_list),
             ('case_id.lawyer_id.id', 'in', lawyer_list)])]
        evidence_list = [evidence.id for evidence in
                         request.env['legal.evidence'].search(
                             [('case_id.id', 'in', case_list)])]
        return {'total_case': case_list,
                'total_invoiced': round(inv_amt, 4),
                'lawyers': lawyer_ids,
                'evidences': evidence_list,
                'trials': trial_list,
                'clients': clients }
