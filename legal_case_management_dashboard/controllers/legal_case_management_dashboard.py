# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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


class LegalCaseDashboard(http.Controller):
    """
    Legal Case Dashboard Controller
    This controller provides JSON endpoints to retrieve data for the
    Legal Case Management Dashboard. It handles the preparation of
    case-related statistics, invoice summaries, and chart datasets
    required for rendering the dashboard in the frontend.
    """

    @http.route('/case/dashboard', type='json', auth='user')
    def get_legal_case_dashboard_values(self, **kwargs):
        """
        Fetch dashboard data including case statistics, invoice details,
        chart data, and summary counts without applying filters.
        """
        moves, invoice_records, client, invoice_data = [], [], [], []
        monthly_income_data = [['Month', 'Income']]
        stage_count_data = [['Stage', 'Cases']]
        case_category_data = [['Category', 'Number']]
        lawyer_object = None
        draft_count, in_progress_count, invoiced_count, reject_count = 0, 0, 0, 0
        won_count, lost_count, cancel_count, invoice_amount = 0, 0, 0, 0
        today_date = fields.Date.today()
        company_id = int(kwargs.get('current_company_id'))
        cases = request.env['case.registration'].search([
            ('company_id', 'in', [company_id, False])
        ])
        # Generate last 12 months range for bar chart
        for num in range(0, 13):
            month_sub = timedelta(days=num * 30)
            current_first_date = today_date.replace(day=5)
            range_date = current_first_date - month_sub
            first_day = range_date.replace(day=1)
            last_day = range_date.replace(day=1) + timedelta(days=32)
            last_day = last_day.replace(day=1) - timedelta(days=1)
            month_name = range_date.strftime("%b")
            monthly_invoice = 0
            for invoice in request.env['account.move'].search([
                ('company_id', 'in', [company_id, False])
            ]):
                if invoice.case_ref:
                    inv_date = invoice.invoice_date
                    if first_day < inv_date < last_day:
                        monthly_invoice += invoice.amount_total
            monthly_income_data.append([month_name, monthly_invoice])
        # Calculate case count for each category
        for category_id in request.env['case.category'].search([]):
            case_count = request.env['case.registration'].search_count([
                ('company_id', 'in', [company_id, False]),
                ('case_category_id', '=', category_id.id)])
            case_category_data.append([category_id.name, case_count])
        invoices = request.env['account.move'].search([])
        for case in cases:
            for invoice in invoices:
                if case.name == invoice.case_ref:
                    # Store case name and corresponding invoice amount
                    invoice_data.append([case.name, invoice.amount_total])
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
            for invoice in request.env['account.move'].search([('case_ref', '=', case.name)]):
                invoice_records.append(invoice)
                moves.append(invoice.id)
                invoice_amount += invoice.amount_total
        case_dict = {}
        for case, amount in invoice_data:
            if case in case_dict:
                case_dict[case] += amount  # add amount to existing case
            else:
                case_dict[case] = amount  # add new case to dictionary
        # Aggregate total invoice amount per case
        total_inv_lis = [[case, amount] for case, amount in case_dict.items()]
        sorted_cases = sorted(total_inv_lis, key=lambda case: case[1],
                              reverse=True)
        top_10_cases = sorted_cases[:10]
        # Append count of each stage to stage_count_data
        stage_count_data.append(['Draft', draft_count])
        stage_count_data.append(['In Progress', in_progress_count])
        stage_count_data.append(['Invoiced', invoiced_count])
        stage_count_data.append(['Reject', reject_count])
        stage_count_data.append(['Won', won_count])
        stage_count_data.append(['Lost', lost_count])
        stage_count_data.append(['Cancel', cancel_count])
        evidence = request.env['legal.evidence'].search([])
        trial = request.env['legal.trial'].search([])
        lawyers = request.env['hr.employee'].search([
            ('is_lawyer', '=', True)
        ])
        # Get lawyer record IDs
        lawyer_list = lawyers.ids
        top_10_cases.insert(0, ['Case', 'Revenue'])
        user_id = request.env.uid
        login_user = request.env['res.users'].search(
            [('employee_id.user_id', '=', user_id)
        ])
        if login_user.has_group('legal_case_management.lawyer_access'):
            if not login_user.has_group('legal_case_management.admin_access'):
                lawyer_object = login_user.employee_id
            else:
                lawyer_object = None
        result = {
            'total_case': len(cases),
            'invoices': invoice_records,
            'total_invoiced': round(invoice_amount, 4),
            'lawyers': len(lawyer_list),
            'lawyer_ids': lawyer_list,
            'evidences': len(evidence),
            'trials': len(trial),
            'clients': len(list(set(client))),
            'clients_in_case': client,
            'case_category': case_category_data,
            'data_list': monthly_income_data,
            'stage_count': stage_count_data,
            'invoice_list': total_inv_lis,
            'top_10_cases': top_10_cases,
            'user_id': user_id,
            'lawyer_object': lawyer_object,
        }
        return result

    @http.route('/selection/field/lawyer', type='json', auth='user',
                csrf=False)
    def add_lawyer_selection_field(self):
        """
        Return list of lawyers for selection field in dashboard filter.
        """
        return [{'name': lawyer.name,
                 'id': lawyer.id
                 } for lawyer in request.env['hr.employee'].search(
            [('is_lawyer', '=', True)])]

    def date_filter(self):
        """
        Generate date ranges for dashboard filters.
        """
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

    @http.route('/dashboard/without/filter', type='json', auth='user')
    def fetch_dashboard_without_filter_value(self, **kw):
        """
        Fetch summary dashboard metrics without applying any filters.
        """
        company_id = int(kw.get('current_company_id'))
        case_count = request.env['case.registration'].search_count([
            ('company_id', 'in', [company_id, False])
        ])
        registration_ids = request.env['case.registration'].search(
            [('state', 'in', ['in_progress','won','invoiced']),
            ('company_id', 'in', [company_id, False])]
        )
        invoice_amount = 0
        for registration_id in registration_ids:
            invoice_amount += sum(request.env['account.move'].search(
                [('case_ref', '=', registration_id.name)]).mapped(
                'amount_total'))
        lawyers = request.env['hr.employee'].search_count(
            [('is_lawyer', '=', True),('company_id', 'in', [company_id, False])])
        evidences = request.env['legal.evidence'].search_count([])
        trials = request.env['legal.trial'].search_count([
            ('case_id.company_id', 'in', [company_id, False])
        ])
        clients = request.env['res.partner'].search_count([
            ('company_id', 'in', [company_id, False])
        ])
        return {'total_case': case_count,
                'total_invoiced': invoice_amount,
                'lawyers': lawyers,
                'evidences': evidences,
                'trials': trials,
                'clients': clients
        }

    @http.route('/dashboard/filter', type='json', auth='user')
    def fetch_dashboard_filter_value(self, **kw):
        """Lawyer wise and stage wise filter"""
        trial_list, clients, case_list, evidence_list, lawyer_ids, invoice_amount = [], \
            [], [], [], [], 0
        data = kw['data']
        if not data.get('stage'):
            stage_list = ['draft', 'in_progress', 'invoiced', 'won', 'lost',
                          'cancel']
        else:
            stage_list = [data['stage']]
        if data['lawyer'] == 'admin':
            lawyer_list = [lawyer.id for lawyer in
                           request.env['hr.employee'].search(
                               [('is_lawyer', '=', True)])]
        else:
            lawyer = [int(data['lawyer'])]
            lawyer_list = [lawyer.id for lawyer in
                           request.env['hr.employee'].search(
                               [('id', 'in', lawyer)])]
        if data.get('month_wise'):
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
                     ('lawyer_id', 'in', [lawyer_list])])
                lawyer_list = [lawyer.id for lawyer in
                               request.env['hr.employee'].search(
                                   [('id', '=', lawyer_list)])]
        else:
            if data['lawyer'] == 'admin':
                registration_ids = request.env['case.registration'].search(
                    [('state', 'in', stage_list)])
                lawyer_list = [lawyer.id for lawyer in
                               request.env['hr.employee'].search(
                                   [('is_lawyer', '=', True)])]
            else:
                registration_ids = request.env['case.registration'].search(
                    [('state', 'in', stage_list),
                     ('lawyer_id', 'in', lawyer_list)])
        for registration_id in registration_ids:
            lawyer_ids.append(registration_id.lawyer_id.id)
            case_list.append(registration_id.id)
            clients.append(registration_id.client_id.id)
            invoice_amount += sum(request.env['account.move'].search(
                [('case_ref', '=', registration_id.name)]).mapped(
                'amount_total'))
        trial_list = [trial.id for trial in request.env['legal.trial'].search(
            [('case_id', 'in', case_list),
             ('case_id.lawyer_id', 'in', lawyer_list)])]
        evidence_list = [evidence.id for evidence in
                         request.env['legal.evidence'].search(
                             [('case_id', 'in', case_list)])]
        return {
            'total_case': case_list,
            'total_invoiced': round(invoice_amount, 4),
            'lawyers': lawyer_ids,
            'evidences': evidence_list,
            'trials': trial_list,
            'clients': clients
        }
