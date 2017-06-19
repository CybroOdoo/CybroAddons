# -*- coding: utf-8 -*-

##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2016-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Niyas Raphy(<https://www.cybrosys.com>)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################
from time import gmtime, strftime
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class CrmReportWonLost(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, lines):
        current_date = strftime("%Y-%m-%d", gmtime())
        logged_users = self.env['res.users'].search([('id', '=', data['create_uid'][0])])
        sheet = workbook.add_worksheet()
        format1 = workbook.add_format({'font_size': 16, 'align': 'vcenter', 'bg_color': '#D3D3D3', 'bold': True})
        format3 = workbook.add_format({'font_size': 10, 'bold': True})
        format4 = workbook.add_format({'font_size': 10})
        format5 = workbook.add_format({'font_size': 10, 'bg_color': '#FFFFFF'})
        format7 = workbook.add_format({'font_size': 12, 'bg_color': '#eaeae1'})
        format8 = workbook.add_format({'font_size': 10, 'bg_color': '#D3D3D3'})
        format9 = workbook.add_format({'font_size': 10, 'align': 'vcenter', 'bg_color': '#ff1a1a', 'bold': True})
        format10 = workbook.add_format({'font_size': 10, 'bg_color': '#00ff00'})
        format11 = workbook.add_format({'font_size': 10, 'bg_color': '#ff0000'})
        justify = workbook.add_format({'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        sheet.merge_range('A1:B1', logged_users.company_id.name, format5)
        sheet.merge_range('A2:M2', logged_users.company_id.street, format5)
        sheet.write('A3', logged_users.company_id.city, format5)
        sheet.merge_range('B3:N3', logged_users.company_id.zip, format5)
        sheet.merge_range('A4:B4', logged_users.company_id.state_id.name, format5)
        sheet.merge_range('A5:B5', logged_users.company_id.country_id.name, format5)
        sheet.merge_range('M1:N1', logged_users.company_id.rml_header1, format5)
        sheet.write('M4', "From Date:", format5)
        if data['start_date']:
            sheet.write('N4', data['start_date'], format5)
        else:
            sheet.write('N4', '', format5)
        sheet.write('M5', 'To Date:', format5)
        if data['end_date']:
            sheet.write('N5', data['end_date'], format5)
        else:
            sheet.write('N5', current_date, format5)
        sheet.merge_range(0, 2, 4, 11, "", format5)
        sheet.merge_range(1, 2, 2, 13, "", format5)
        sheet.merge_range(1, 6, 4, 8, "", format5)
        irow = 5
        icol = 0
        sheet.merge_range(irow, icol, irow+2, icol + 13, 'CRM WON/LOST REPORT', format1)
        sheet.merge_range('A9:B9', "Sales Person", format7)
        sheet.write('C9', "Status", format7)
        sheet.merge_range('D9:G9', "Lead Name", format7)
        sheet.write('H9', "Exp. Rev", format7)
        sheet.merge_range('I9:K9', "Reason", format7)
        sheet.merge_range('L9:N9', "Internal Note", format7)
        sales_person = []
        if data['sales_person']:
            for user_sales in data['sales_person']:
                sales_person.append(user_sales)
        else:
            res_users = self.env['res.users'].search([])
            for users in res_users:
                sales_person.append(users.id)
        irow = 8
        icol = 0
        for person in sales_person:
            lost_list = []
            sale_users = self.env['res.users'].search([('id', '=', person)])
            lost_leads = self.env['crm.lead'].search([('active', '=', False)])
            if data['start_date'] and data['end_date']:
                crm_stages = self.env['crm.lead'].search([('user_id', '=', person),
                                                          ('date_closed', '>=', data['start_date']),
                                                          ('date_closed', '<=', data['end_date'])])

                for lost in lost_leads:
                    if lost.user_id.id == person:
                        if lost.create_date >= data['start_date'] and lost.create_date < data['end_date']:
                            lost_list.append(lost.id)
            elif data['start_date'] and not data['end_date']:
                crm_stages = self.env['crm.lead'].search([('user_id', '=', person),
                                                          ('date_closed', '>=', data['start_date'])])
                for lost in lost_leads:
                    if lost.user_id.id == person:
                        if lost.create_date >= data['start_date']:
                            lost_list.append(lost.id)
            elif not data['start_date'] and data['end_date']:
                crm_stages = self.env['crm.lead'].search([('user_id', '=', person),
                                                          ('date_closed', '<=', data['end_date'])])
                for lost in lost_leads:
                    if lost.user_id.id == person:
                        if lost.create_date < data['end_date']:
                            lost_list.append(lost.id)
            else:
                crm_stages = self.env['crm.lead'].search([('user_id', '=', person)])
                for lost in lost_leads:
                    if lost.user_id.id == person:
                            lost_list.append(lost.id)
            if crm_stages or lost_list:
                irow += 1
                sheet.merge_range(irow, icol, irow, icol + 1, sale_users.partner_id.name, format8)
                sheet.write(irow, icol + 2, '', format8)
                sheet.merge_range(irow, icol+3, irow, icol + 6, '', format8)
                sheet.write(irow, icol + 7, '', format8)
                sheet.merge_range(irow, icol + 8, irow, icol+10, '', format8)
                sheet.merge_range(irow, icol + 11, irow, icol + 13, '', format8)
                won_list = []
                for stages in crm_stages:
                    if stages.active and stages.date_closed:
                        won_list.append(stages.id)
                if won_list:
                    irow += 1
                    icol = 0
                    sheet.merge_range(irow, icol, irow, icol + 1, '', format3)
                    sheet.write(irow, icol + 2, 'Won', format10)
                    sheet.merge_range(irow, icol + 3, irow, icol + 6, '', format3)
                    sheet.write(irow, icol + 7, '', format3)
                    sheet.merge_range(irow, icol + 8, irow, icol + 10, '', format3)
                    sheet.merge_range(irow, icol + 11, irow, icol + 13, '', format3)
                    for won_leads in won_list:
                        lead_won = self.env['crm.lead'].search([('id', '=', won_leads)])
                        irow += 1
                        icol = 0
                        sheet.merge_range(irow, icol, irow, icol + 1, '', format3)
                        sheet.write(irow, icol + 2, '', format3)
                        sheet.merge_range(irow, icol + 3, irow, icol + 6, lead_won.name, format4)
                        if lead_won.planned_revenue:
                            sheet.write(irow, icol + 7, lead_won.planned_revenue, format4)
                        else:
                            sheet.write(irow, icol + 7, '', format4)
                        sheet.merge_range(irow, icol + 8, irow, icol + 10, '', format4)
                        if lead_won.description:
                            sheet.merge_range(irow, icol + 11, irow, icol + 13, lead_won.description, format4)
                        else:
                            sheet.merge_range(irow, icol + 11, irow, icol + 13, '', format4)

                if lost_list:
                    irow += 1
                    icol = 0
                    sheet.merge_range(irow, icol, irow, icol + 1, '', format3)
                    sheet.write(irow, icol + 2, 'Lost', format11)
                    sheet.merge_range(irow, icol + 3, irow, icol + 6, '', format3)
                    sheet.write(irow, icol + 7, '', format3)
                    sheet.merge_range(irow, icol + 8, irow, icol + 10, '', format3)
                    sheet.merge_range(irow, icol + 11, irow, icol + 13, '', format3)
                    all_lead_lost = self.env['crm.lead'].search([('active', '=', False)])
                    for lost_leads in all_lead_lost:
                        if lost_leads.lost_reason:
                            get_lost_reason = self.env['crm.lost.reason'].search([('id', '=', lost_leads.lost_reason.id)])
                            reason_lost = get_lost_reason.name
                        if lost_leads.id in lost_list:
                            irow += 1
                            icol = 0
                            sheet.merge_range(irow, icol, irow, icol + 1, '', format3)
                            sheet.write(irow, icol + 2, '', format3)
                            sheet.merge_range(irow, icol + 3, irow, icol + 6, lost_leads.name, format4)
                            if lost_leads.planned_revenue:
                                sheet.write(irow, icol + 7, lost_leads.planned_revenue, format4)
                            else:
                                sheet.write(irow, icol + 7, '', format4)
                            if lost_leads.lost_reason:
                                sheet.merge_range(irow, icol + 8, irow, icol + 10, reason_lost, format4)
                            else:
                                sheet.merge_range(irow, icol + 8, irow, icol + 10, '', format4)
                            if lost_leads.description:
                                sheet.merge_range(irow, icol + 11, irow, icol + 13, lost_leads.description, format4)
                            else:
                                sheet.merge_range(irow, icol + 11, irow, icol + 13, '', format4)
                if not won_list and not lost_list:
                    sheet.merge_range(irow + 1, icol, irow + 2, icol + 13, 'No Won/Lost Leads', format9)
                    irow += 2
        sheet.merge_range(irow + 1, icol, irow + 2, icol + 13, '', format1)

CrmReportWonLost('report.crm_won_lost_report.report_crm_won_lost_report.xlsx', 'crm.won.lost.report')