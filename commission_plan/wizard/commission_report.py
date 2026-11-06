# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
import io
import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import json_default

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class CommissionReport(models.TransientModel):
    """The commission.report model is created and shown as the wizard window"""
    _name = 'commission.report'
    _description = 'Commission Report'

    date_from = fields.Date(string="From Date",
                            help="The date from report is needed")
    date_to = fields.Date(string="To Date", help="The date to report is needed")
    salesperson_ids = fields.Many2many('res.users',
                                       domain="[('share','=',False)]",
                                       help="Salespersons of the corresponding "
                                            "reports")
    sales_team_ids = fields.Many2many('crm.team',
                                      help="Sales teams of the corresponding "
                                           "reports")
    date = fields.Date(default=fields.Date.context_today,
                       help="Current date")
    is_sales_person = fields.Boolean(default=False, string="Is sales person",
                                     help="Whether the report is for sales "
                                          "person")
    is_sales_team = fields.Boolean(default=False, string="Is sales team",
                                   help="Whether the report is for sales team")

    @api.onchange('salesperson_ids')
    def _onchange_salesperson_ids(self):
        """Function for hide a field base on values"""
        self.is_sales_person = bool(self.salesperson_ids)

    @api.onchange('sales_team_ids')
    def _onchange_sales_team_ids(self):
        """Function for hide a field base on values"""
        self.is_sales_team = bool(self.sales_team_ids)

    @api.constrains('sales_team_ids', 'salesperson_ids')
    def sales_team_constrains(self):
        """Function for showing validation error"""
        for rec in self:
            if self.sales_team_ids:
                if not rec.sales_team_ids.member_ids:
                    raise ValidationError(self.env._(
                        "Selected Sales Team haven't any Salespersons"))
                if not self.sales_team_ids.member_ids.commission_id and \
                        not self.sales_team_ids.commission_id:
                    raise ValidationError(self.env._(
                        "Selected Sales Team haven't any Commission Plan"))
            elif self.salesperson_ids and not (
                    rec.salesperson_ids.commission_id or
                    rec.salesperson_ids.sale_team_id.commission_id):
                raise ValidationError(self.env._(
                    "Selected Salesperson haven't any Commission Plan"))

    def action_print_xlsx_report(self):
        """Print the commission rows persisted against sale orders."""
        total_list = []
        commission_list = []
        user_commission_name = []
        user_commission_salesperson = []
        user_commission_sale_order = []
        user_commission_kind = []
        commission_total = []
        commission = []
        commission_name = []
        commission_salesperson = []
        commission_sales_team = []
        commission_sale_order = []
        commission_kind = []

        # The XLSX renderer shows either the salesperson section or the sales
        # team section, so fetch only the section selected by the user.
        if self.salesperson_ids:
            for line in self._fetch_stored_commissions(
                    user_ids=self.salesperson_ids.ids):
                user_commission_name.append(line['commission_name'])
                user_commission_salesperson.append(line['salesperson'])
                user_commission_sale_order.append(line['sale_order'])
                # Earned and Return are kept as separate rows (never netted
                # together into one line), so this column is what tells them
                # apart in the printed sheet -- without it a full return
                # looks like the earned row simply vanished.
                user_commission_kind.append(
                    self.env._('Return') if line['commission_type'] == 'return'
                    else self.env._('Earned'))
                total_list.append(line['revenue'])
                commission_list.append(line['amount'])
        else:
            # With no explicit filter, show all persisted commission rows in
            # the sales-team section.
            teams = self.sales_team_ids
            for line in self._fetch_stored_commissions(
                    team_ids=teams.ids if teams else None,
                    all_teams=not teams):
                commission_name.append(line['commission_name'])
                commission_salesperson.append(line['salesperson'])
                commission_sales_team.append(line['sales_team'])
                commission_sale_order.append(line['sale_order'])
                commission_kind.append(
                    self.env._('Return') if line['commission_type'] == 'return'
                    else self.env._('Earned'))
                commission_total.append(line['revenue'])
                commission.append(line['amount'])
        # Raise a user-facing error only after the fetch so that the
        # report wizard can be opened and submitted even when there is
        # genuinely nothing to display yet (e.g. in automated tests).
        if not commission_list and not commission:
            raise ValidationError(self.env._("No data found."))
        data = {
            'model_id': self.id,
            'date': self.date,
            'date_from': self.date_from,
            'date_to': self.date_to,
            # The renderer uses this value as a section flag.  When no team
            # filter is selected, persisted rows still make the team section
            # applicable.
            'sales_team_ids': (self.sales_team_ids.ids or
                               ([1] if commission_sales_team else [])),
            'salesperson_ids': self.salesperson_ids.ids,
            'commission_list': commission_list,
            'total_list': total_list,
            'commission': commission,
            'commission_total': commission_total,
            'commission_name': commission_name,
            'commission_salesperson': commission_salesperson,
            'commission_sales_team': commission_sales_team,
            'commission_sale_order': commission_sale_order,
            'commission_kind': commission_kind,
            'user_commission_name': user_commission_name,
            'user_commission_salesperson': user_commission_salesperson,
            'user_commission_sale_order': user_commission_sale_order,
            'user_commission_kind': user_commission_kind,
        }
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'commission.report',
                'options': json.dumps(data, default=json_default),
                'output_format': 'xlsx',
                'report_name': 'Commission Plan xlsx report'},
            'report_type': 'xlsx'
        }

    def _fetch_stored_commissions(self, user_ids=None, team_ids=None,
                                  all_teams=False):
        """Fetch persisted commissions with SQL for the XLSX report."""
        # This method bypasses the ORM with raw SQL.  Flush the commission
        # model first so freshly created lines have their stored related
        # fields (notably company_id and order_date) written before the
        # company/date filters below are evaluated.
        self.env['sale.order.commission'].flush_model()
        query = """
            SELECT soc.revenue, soc.amount, soc.commission_type,
                   so.name AS sale_order,
                   cc.name AS commission_name,
                   rp.name AS salesperson,
                   COALESCE(ct.name->>%s, ct.name->>'en_US') AS sales_team
              FROM sale_order_commission soc
              JOIN crm_commission cc ON cc.id = soc.commission_id
              JOIN res_users ru ON ru.id = soc.user_id
              JOIN res_partner rp ON rp.id = ru.partner_id
              JOIN sale_order so ON so.id = soc.order_id
              LEFT JOIN crm_team ct ON ct.id = soc.team_id
             WHERE soc.company_id = ANY(%s)
        """
        lang = self.env.lang or 'en_US'
        params = [lang, self.env.companies.ids]
        if self.date_from:
            query += " AND soc.order_date >= %s"
            params.append(self.date_from)
        if self.date_to:
            query += " AND soc.order_date < %s"
            params.append(fields.Date.add(self.date_to, days=1))
        if user_ids is not None:
            if user_ids:
                query += " AND soc.user_id = ANY(%s)"
                params.append(user_ids)
            else:
                query += " AND FALSE"
        if team_ids is not None and not all_teams:
            if team_ids:
                query += " AND soc.team_id = ANY(%s)"
                params.append(team_ids)
            else:
                query += " AND FALSE"
        query += " ORDER BY soc.order_date, soc.id"
        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()
        return result

    def get_xlsx_report(self, data, response):
        """get_xlsx_report function"""
        date = data['date']
        team = data['sales_team_ids']
        user = data['salesperson_ids']
        commission_list = data['commission_list']
        total_list = data['total_list']
        commission = data['commission']
        commission_total = data['commission_total']
        commission_name = data['commission_name']
        commission_salesperson = data['commission_salesperson']
        commission_sales_team = data['commission_sales_team']
        commission_sale_order = data['commission_sale_order']
        commission_kind = data['commission_kind']
        user_commission_name = data['user_commission_name']
        user_commission_salesperson = data['user_commission_salesperson']
        user_commission_sale_order = data['user_commission_sale_order']
        user_commission_kind = data['user_commission_kind']
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '15px', 'valign': 'vcenter',
                                    'bg_color': 'orange',
                                    'font_color': 'white'})
        format1 = workbook.add_format({'align': 'left', 'font_size': '12px'})
        format2 = workbook.add_format({'align': 'right', 'font_size': '12x'})
        format3 = workbook.add_format(
            {'align': 'right', 'font_size': '12x', 'bold': True})
        # Return rows are the negative claw-back entries -- flagged in red
        # so they read as a distinct, deliberate reversal rather than as
        # the earned row having been overwritten or lost.
        format_return = workbook.add_format(
            {'align': 'right', 'font_size': '12x', 'font_color': 'red'})
        format1_return = workbook.add_format(
            {'align': 'left', 'font_size': '12px', 'font_color': 'red'})
        heading = workbook.add_format({'align': 'left', 'bold': True,
                                       'font_size': '12px',
                                       'valign': 'vcenter'})
        date_format = workbook.add_format(
            {'num_format': 'dd/mm/yy', 'align': 'left', 'font_size': '10px'})
        sheet.merge_range('A2:B2', "Printed Date: " + date, date_format)
        sheet.write('A4', 'No.', heading)
        sheet.set_column(5, 1, 25)
        sheet.set_row(0, 25)
        row = 5
        col = 0
        index = 1
        if user:
            sheet.merge_range('A1:G1', 'COMMISSION PLAN REPORT', head)
            if data.get('date_from'):
                sheet.write('F2', 'Date From: ' + data['date_from'],
                            date_format)
            if data.get('date_to'):
                sheet.write('G2', 'Date To: ' + data['date_to'], date_format)
            sheet.write('B4', 'Sale Persons', heading)
            sheet.write('C4', 'Sale Order', heading)
            sheet.write('D4', 'Commission Plan Name', heading)
            sheet.write('E4', 'Type', heading)
            sheet.write('F4', 'Total Revenue', heading)
            sheet.write('G4', 'Commission Amount', heading)
            for j, kind in zip(user_commission_salesperson,
                               user_commission_kind):
                fmt = format1_return if kind == self.env._('Return') else format1
                sheet.write(row, col + 0, index, format2)
                sheet.write(row, col + 1, j, fmt)
                row += 1
                index += 1
            row = 5
            col = 0
            for j, kind in zip(user_commission_sale_order,
                               user_commission_kind):
                fmt = format1_return if kind == self.env._('Return') else format1
                sheet.write(row, col + 2, j, fmt)
                row += 1
            row = 5
            col = 0
            for j, kind in zip(user_commission_name, user_commission_kind):
                fmt = format1_return if kind == self.env._('Return') else format1
                sheet.write(row, col + 3, j, fmt)
                row += 1
            row = 5
            col = 0
            for kind in user_commission_kind:
                fmt = format1_return if kind == self.env._('Return') else format1
                sheet.write(row, col + 4, kind, fmt)
                row += 1
            row = 5
            col = 0
            for j, kind in zip(total_list, user_commission_kind):
                fmt = format_return if kind == self.env._('Return') else format2
                sheet.write(row, col + 5, round(j, 2), fmt)
                row += 1
            row = 5
            col = 0
            for i, kind in zip(commission_list, user_commission_kind):
                fmt = format_return if kind == self.env._('Return') else format2
                sheet.write(row, col + 6, round(i, 2), fmt)
                row += 1
            earned_total = sum(
                i for i, kind in zip(commission_list, user_commission_kind)
                if kind == self.env._('Earned'))
            return_total = sum(
                i for i, kind in zip(commission_list, user_commission_kind)
                if kind == self.env._('Return'))
            sheet.write(row + 1, col + 5, 'Total Earned:', format3)
            sheet.write(row + 1, col + 6, round(earned_total, 2), format2)
            sheet.write(row + 2, col + 5, 'Total Returns:', format3)
            sheet.write(row + 2, col + 6, round(return_total, 2),
                        format_return)
            sheet.write(row + 3, col + 5, 'Net Total:', format3)
            sheet.write(row + 3, col + 6, round(sum(commission_list), 2),
                        format3)
        elif team:
            sheet.merge_range('A1:H1', 'COMMISSION PLAN REPORT', head)
            if data.get('date_from'):
                sheet.write('G2', 'Date From: ' + data['date_from'],
                            date_format)
            if data.get('date_to'):
                sheet.write('H2', 'Date To: ' + data['date_to'], date_format)
            sheet.write('B4', 'Sales Teams', heading)
            sheet.write('C4', 'Sales Person', heading)
            sheet.write('D4', 'Sale Order', heading)
            sheet.write('E4', 'Commission Plan Name', heading)
            sheet.write('F4', 'Type', heading)
            sheet.write('G4', 'Total Revenue', heading)
            sheet.write('H4', 'Commission Amount', heading)
            for j, kind in zip(commission_sales_team, commission_kind):
                fmt = format1_return if kind == self.env._('Return') else format1
                sheet.write(row, col + 0, index, format2)
                sheet.write(row, col + 1, j, fmt)
                row += 1
                index += 1
            row = 5
            col = 0
            for j, kind in zip(commission_salesperson, commission_kind):
                fmt = format1_return if kind == self.env._('Return') else format1
                sheet.write(row, col + 2, j, fmt)
                row += 1
            row = 5
            col = 0
            for j, kind in zip(commission_sale_order, commission_kind):
                fmt = format1_return if kind == self.env._('Return') else format1
                sheet.write(row, col + 3, j, fmt)
                row += 1
            row = 5
            col = 0
            for j, kind in zip(commission_name, commission_kind):
                fmt = format1_return if kind == self.env._('Return') else format1
                sheet.write(row, col + 4, j, fmt)
                row += 1
            row = 5
            col = 0
            for kind in commission_kind:
                fmt = format1_return if kind == self.env._('Return') else format1
                sheet.write(row, col + 5, kind, fmt)
                row += 1
            row = 5
            col = 0
            for j, kind in zip(commission_total, commission_kind):
                fmt = format_return if kind == self.env._('Return') else format2
                sheet.write(row, col + 6, round(j, 2), fmt)
                row += 1
            row = 5
            col = 0
            for i, kind in zip(commission, commission_kind):
                fmt = format_return if kind == self.env._('Return') else format2
                sheet.write(row, col + 7, round(i, 2), fmt)
                row += 1
            earned_total = sum(
                i for i, kind in zip(commission, commission_kind)
                if kind == self.env._('Earned'))
            return_total = sum(
                i for i, kind in zip(commission, commission_kind)
                if kind == self.env._('Return'))
            sheet.write(row + 1, col + 4, 'Total Earned:', format3)
            sheet.write(row + 1, col + 7, round(earned_total, 2), format2)
            sheet.write(row + 2, col + 4, 'Total Returns:', format3)
            sheet.write(row + 2, col + 7, round(return_total, 2),
                        format_return)
            sheet.write(row + 3, col + 4, 'Net Total:', format3)
            sheet.write(row + 3, col + 7, round(sum(commission), 2),
                        format3)
        sheet.autofit()
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def _calculate_product_commission(self, filtered_order_lines,
                                      total_list, commission_list,
                                      user_commission_salesperson, *args):
        """Returns the calculated product commission"""
        user, commission_id, user_commission_name = args
        commission_products = commission_id.product_comm_ids.mapped(
            'product_id')
        commission_category = commission_id.product_comm_ids.mapped(
            'category_id')
        prod_commission = filtered_order_lines.filtered(
            lambda
                rec: rec.product_id.id in commission_products.ids or
                     rec.product_id.categ_id.id in commission_category.ids
        )
        for rule in commission_id.product_comm_ids:
            product_order_line = prod_commission.filtered(
                lambda rec: rec.product_id == rule.product_id or
                            rec.product_id.categ_id.id == rule.category_id.id)
            total_price = sum(product_order_line.mapped('price_subtotal'))
            product_commission = (total_price * rule.percentage) / 100 if \
                rule.commission_amount_type == 'percentage' else \
                rule.fixed_amount
            total_list.append(total_price)
            user_commission_name.append(commission_id.name)
            user_commission_salesperson.append(user.name)
            commission_list.append(
                rule.amount if product_commission > rule.amount and
                               rule.commission_amount_type == 'percentage'
                else product_commission
            )

    def _calculate_graduated_commission(self,
                                        commission_list,
                                        user_commission_salesperson,
                                        total_list, *args
                                        ):
        """Returns the calculated Graduated commission"""
        user, commission_id, rule, filtered_order_lines_commission_total, \
            user_commission_name = args
        graduated_commission = (
                                       filtered_order_lines_commission_total
                                       * rule.graduated_commission_rate
                               ) / 100 if rule.amount_from \
                <= filtered_order_lines_commission_total < rule.amount_to else \
            rule.graduated_fixed_amount
        commission_list.append(graduated_commission)
        user_commission_name.append(commission_id.name)
        user_commission_salesperson.append(user.name)
        total_list.append(filtered_order_lines_commission_total)

    def _calculate_straight_commission(self, commission_id,
                                       filtered_order_lines_commission_total,
                                       commission_list,
                                       *args):
        """Returns the calculated Straight commission"""
        user_commission_name, \
            user_commission_salesperson, total_list, user = args
        straight_commission = (
                                      filtered_order_lines_commission_total
                                      * commission_id.straight_commission_rate
                              ) / 100 if \
            commission_id.straight_commission_type == 'percentage' else \
            commission_id.straight_commission_fixed
        commission_list.append(straight_commission)
        user_commission_name.append(commission_id.name)
        user_commission_salesperson.append(user.name)
        total_list.append(filtered_order_lines_commission_total)

    def _filter_sale_orders_by_user(self, team_sale_orders, team_user):
        """Returns the filtered team_sale_orders using the team_users"""
        return team_sale_orders.filtered(lambda rec: rec.user_id == team_user)

    def _calculate_commissions(self, team_sale_orders_dict):
        """Returns the calculated commissions"""
        commission_total = []
        commission = []
        commission_name = []
        commission_salesperson = []
        commission_sales_team = []
        for team_user, team_sale_orders in team_sale_orders_dict.items():
            commissions_id = team_user.sale_team_id.commission_id or \
                             team_user.commission_id
            if commissions_id:
                if self.date_to and self.date_from:
                    filtered_order_lines = team_sale_orders.filtered(
                        lambda rec: self.date_from <= rec.date_order.date()
                                    <= self.date_to and rec.date_order.date()
                                    >= commissions_id.date_from
                    ).mapped('order_line')
                elif not self.date_to and self.date_from:
                    filtered_order_lines = team_sale_orders \
                        .filtered(lambda rec: rec.date_order.date() >=
                                              self.date_from >=
                                              commissions_id.date_from) \
                        .mapped('order_line')
                elif self.date_to and not self.date_from:
                    filtered_order_lines = team_sale_orders \
                        .filtered(lambda rec: rec.date_order.date() <=
                                              self.date_to <=
                                              commissions_id.date_to) \
                        .mapped('order_line')
                else:
                    filtered_order_lines = team_sale_orders.mapped(
                        'order_line')
                filtered_order_lines_commission_total = sum(
                    filtered_order_lines.mapped('price_subtotal'))
                if commissions_id.type == 'product':
                    commission_products = commissions_id.product_comm_ids.mapped(
                        'product_id').ids
                    commission_category = commissions_id.product_comm_ids.mapped(
                        'category_id').ids
                    prod_commission = filtered_order_lines.filtered(
                        lambda rec: rec.product_id.id in commission_products or
                                    rec.product_id.categ_id.id in commission_category
                    )
                    for rules in commissions_id.product_comm_ids:
                        product_order_line = prod_commission.filtered(
                            lambda rec: rec.product_id == rules.product_id or
                                        rec.product_id.categ_id.id == rules.category_id.id)
                        total_price = sum(
                            product_order_line.mapped('price_subtotal')
                        )
                        product_commission = (
                                                     total_price * rules.percentage
                                             ) / 100 if \
                            rules.commission_amount_type == 'percentage' else \
                            rules.fixed_amount
                        commission_total.append(total_price)
                        commission_name.append(commissions_id.name)
                        commission_salesperson.append(team_user.name)
                        commission_sales_team.append(
                            team_user.sale_team_id.name)
                        commission.append(
                            rules.amount if product_commission > rules.amount
                                            and rules.commission_amount_type == 'percentage'
                            else product_commission
                        )
                if commissions_id.type == 'revenue' and (
                        commissions_id.revenue_type == 'graduated'):
                    for rules in commissions_id.revenue_grd_comm_ids:
                        if rules.amount_from <= \
                                filtered_order_lines_commission_total \
                                < rules.amount_to:
                            graduated_commission = (
                                   filtered_order_lines_commission_total
                                   * rules.graduated_commission_rate) / 100 if \
                                rules.graduated_amount_type == 'percentage' \
                                else rules.graduated_fixed_amount
                            commission.append(graduated_commission)
                            commission_name.append(commissions_id.name)
                            commission_salesperson.append(team_user.name)
                            commission_sales_team.append(
                                team_user.sale_team_id.name)
                            commission_total.append(
                                filtered_order_lines_commission_total)
                if commissions_id.type == 'revenue' and (
                        commissions_id.revenue_type == 'straight'):
                    straight_commission = (
                                      filtered_order_lines_commission_total
                                      * commissions_id.straight_commission_rate
                                          ) / 100 if \
                        commissions_id.straight_commission_type == \
                        'percentage' else \
                        commissions_id.straight_commission_fixed
                    commission.append(straight_commission)
                    commission_name.append(commissions_id.name)
                    commission_salesperson.append(team_user.name)
                    commission_sales_team.append(team_user.sale_team_id.name)
                    commission_total.append(
                        filtered_order_lines_commission_total
                    )
        return commission_total, commission, commission_name, \
            commission_salesperson, commission_sales_team
