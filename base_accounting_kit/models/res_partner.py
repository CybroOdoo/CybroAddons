# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from datetime import date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import base64
import io
import json
import xlsxwriter
from odoo.exceptions import ValidationError, UserError
from odoo.tools.json import json_default


class ResPartner(models.Model):
    """Inheriting res.partner"""
    _inherit = "res.partner"

    invoice_list = fields.One2many('account.move', 'partner_id',
                                   string="Invoice Details",
                                   readonly=True,
                                   domain=(
                                   [('payment_state', '=', 'not_paid'),
                                    ('move_type', '=', 'out_invoice')]))
    total_due = fields.Monetary(compute='_compute_for_followup', store=False,
                                readonly=True)
    next_reminder_date = fields.Date(compute='_compute_for_followup',
                                     store=False, readonly=True)
    total_overdue = fields.Monetary(compute='_compute_for_followup',
                                    store=False, readonly=True)
    followup_status = fields.Selection(
        [('in_need_of_action', 'In need of action'),
         ('with_overdue_invoices', 'With overdue invoices'),
         ('no_action_needed', 'No action needed')],
        string='Followup status',
        )
    followup_level_id = fields.Many2one(
        'followup.line', string='Follow-up Level', copy=False,
        help="Last follow-up level applied to this customer.")
    latest_followup_date = fields.Date(
        string='Latest Follow-up', copy=False, readonly=True,
        help="Date the last follow-up was sent to this customer.")

    warning_stage = fields.Float(string='Warning Amount',
                                 help="A warning message will appear once the "
                                      "selected customer is crossed warning "
                                      "amount. Set its value to 0.00 to"
                                      " disable this feature")
    blocking_stage = fields.Float(string='Blocking Amount',
                                  help="Cannot make sales once the selected "
                                       "customer is crossed blocking amount."
                                       "Set its value to 0.00 to disable "
                                       "this feature")
    due_amount = fields.Float(string="Total Sale",
                              compute="_compute_due_amount")
    active_limit = fields.Boolean("Active Credit Limit", default=False)

    enable_credit_limit = fields.Boolean(string="Credit Limit Enabled",
                                         compute="_compute_enable_credit_limit")

    def _compute_for_followup(self):
        """
        Compute the fields 'total_due', 'total_overdue' , 'next_reminder_date' and 'followup_status'
        """
        for record in self:
            total_due = 0
            total_overdue = 0
            today = fields.Date.today()
            for am in record.invoice_list:
                if am.company_id == self.env.company:
                    amount = am.amount_residual
                    total_due += amount

                    is_overdue = today > am.invoice_date_due if am.invoice_date_due else today > am.date
                    if is_overdue:
                        total_overdue += amount or 0
            min_date = record.get_min_date()
            action = record.action_after() or 0
            if min_date:
                date_reminder = min_date + timedelta(days=action)
                if date_reminder:
                    record.next_reminder_date = date_reminder
            else:
                date_reminder = today
                record.next_reminder_date = date_reminder
            if total_overdue > 0 and date_reminder > today:
                followup_status = "with_overdue_invoices"
            elif total_due > 0 and date_reminder <= today:
                followup_status = "in_need_of_action"
            else:
                followup_status = "no_action_needed"
            record.total_due = total_due
            record.total_overdue = total_overdue
            record.followup_status = followup_status

    def get_min_date(self):
        """Get the minimum invoice due date from the partner's invoice list."""
        today = date.today()
        for this in self:
            if this.invoice_list:
                min_list = this.invoice_list.mapped('invoice_date_due')
                while False in min_list:
                    min_list.remove(False)
                return min(min_list)
            else:
                return today

    def get_delay(self):
        """Retrieve the delay information for follow-up lines associated with the company."""
        delay = """SELECT fl.id, fl.delay
                    FROM followup_line fl
                    JOIN account_followup af ON fl.followup_id = af.id
                    WHERE af.company_id = %s
                    ORDER BY fl.delay;

                    """
        self.env.cr.execute(delay, [self.env.company.id])
        record = self.env.cr.dictfetchall()

        return record

    def action_after(self):
        """Retrieve the delay information for follow-up lines associated with the company and return the delay value if found."""
        lines = self.env['followup.line'].search([(
            'followup_id.company_id', '=', self.env.company.id)])
        if lines:
            record = self.get_delay()
            for i in record:
                return i['delay']

    # ------------------------------------------------------------------
    # Follow-up escalation & sending
    # ------------------------------------------------------------------
    def _get_followup_lines(self):
        """The company's follow-up levels, ordered by delay (model _order)."""
        return self.env['followup.line'].search(
            [('followup_id.company_id', '=', self.env.company.id)])

    def _max_overdue_days(self):
        """Largest number of days any of the partner's open invoices is overdue."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        overdue = []
        for am in self.invoice_list:
            due = am.invoice_date_due or am.date
            if due and due < today:
                overdue.append((today - due).days)
        return max(overdue) if overdue else 0

    def _get_next_followup_line(self):
        """Return the next escalation level due for this partner, or empty.

        Picks levels whose ``delay`` has been reached by the partner's overdue
        days, and returns the first one *beyond* the level already sent."""
        self.ensure_one()
        days = self._max_overdue_days()
        reached = self._get_followup_lines().filtered(lambda l: l.delay <= days)
        if not reached:
            return self.env['followup.line']
        if not self.followup_level_id:
            return reached[0]
        remaining = reached.filtered(
            lambda l: l.delay > self.followup_level_id.delay)
        return remaining[0] if remaining else self.env['followup.line']

    def _followup_letter_report(self):
        return self.env.ref(
            'base_accounting_kit.action_report_followup_letter',
            raise_if_not_found=False)

    def _send_followup(self, followup_line=None):
        """Send the reminder for the (next) due level: email the customer,
        log it in the chatter and advance the partner's follow-up level.
        Shared by the manual button and the scheduled action."""
        default_template = self.env.ref(
            'base_accounting_kit.mail_template_followup',
            raise_if_not_found=False)
        for partner in self:
            line = followup_line or partner._get_next_followup_line()
            if not line:
                continue
            if line.send_email and partner.email:
                template = line.email_template_id or default_template
                if template:
                    template.send_mail(partner.id, force_send=True)
            partner.write({
                'followup_level_id': line.id,
                'latest_followup_date': fields.Date.context_today(partner),
            })
            partner.message_post(
                body=_("Follow-up '%s' sent to %s.") % (line.name, partner.name))
        return True

    def action_send_followup(self):
        """Manual button: send the due follow-up to the selected partner(s)."""
        self._send_followup()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Follow-up sent.'),
                'type': 'success',
                'sticky': False,
            },
        }

    def action_print_followup_letter(self):
        """Manual button: print the reminder letter (PDF)."""
        self.ensure_one()
        report = self._followup_letter_report()
        if not report:
            raise UserError(_("The follow-up letter report is not available."))
        return report.report_action(self)

    @api.model
    def _cron_send_followups(self):
        """Scheduled action: email the due follow-up to every customer whose
        next escalation level has been reached."""
        today = fields.Date.context_today(self)
        overdue_moves = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '=', 'not_paid'),
            ('state', '=', 'posted'),
            ('invoice_date_due', '<', today),
        ])
        partners = overdue_moves.mapped('partner_id')
        for partner in partners:
            if partner._get_next_followup_line():
                partner._send_followup()

    @api.depends('credit', 'debit')
    def _compute_due_amount(self):
        """Compute function to compute the due amount with the
         credit and debit amount"""
        for rec in self:
            rec.due_amount = rec.credit - rec.debit

    def _compute_enable_credit_limit(self):
        """ Check credit limit is enabled in account settings """
        params = self.env['ir.config_parameter'].sudo()
        customer_credit_limit = params.get_param('customer_credit_limit',
                                                 default=False)
        for rec in self:
            rec.enable_credit_limit = True if customer_credit_limit else False

    @api.constrains('warning_stage', 'blocking_stage')
    def constrains_warning_stage(self):
        """Constrains functionality used to indicate or raise an
        UserError"""
        for rec in self:
            if rec.active_limit and rec.enable_credit_limit:
                if rec.warning_stage >= rec.blocking_stage:
                    if rec.blocking_stage > 0:
                        raise UserError(_(
                            "Warning amount should be less than Blocking amount"))

    # customer statement

    customer_report_ids = fields.Many2many(
        'account.move',
        compute='_compute_customer_report_ids',
        help='Partner Invoices related to Customer')
    vendor_statement_ids = fields.Many2many(
        'account.move',
        compute='_compute_vendor_statement_ids',
        help='Partner Bills related to Vendor')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id.id,
        help="currency related to Customer or Vendor")

    def _compute_customer_report_ids(self):
        """ For computing 'invoices' of partner """
        for rec in self:
            inv_ids = self.env['account.move'].search(
                [('partner_id', '=', rec.id),
                 ('move_type', '=', 'out_invoice'),
                 ('payment_state', '!=', 'paid'),
                 ('state', '=', 'posted')])
            rec.customer_report_ids = inv_ids

    def _compute_vendor_statement_ids(self):
        """ For computing 'bills' of partner """
        for rec in self:
            bills = self.env['account.move'].search(
                [('partner_id', '=', rec.id),
                 ('move_type', '=', 'in_invoice'),
                 ('payment_state', '!=', 'paid'),
                 ('state', '=', 'posted')])
            rec.vendor_statement_ids = bills

    def main_query(self):
        """ Return select query (parameters: partner id, company id) """
        query = """SELECT name , invoice_date, invoice_date_due,
                       amount_total_signed AS sub_total,
                       amount_residual_signed AS amount_due ,
                       amount_residual AS balance
               FROM account_move WHERE payment_state != 'paid'
               AND state ='posted' AND partner_id = %s
               AND company_id = %s """
        return query

    def amount_query(self):
        """ Return query for calculating total amount
        (parameters: partner id, company id) """
        amount_query = """ SELECT SUM(amount_total_signed) AS total,
                       SUM(amount_residual) AS balance
                   FROM account_move WHERE payment_state != 'paid'
                   AND state ='posted' AND partner_id = %s
                   AND company_id = %s """
        return amount_query

    def action_share_pdf(self):
        """ Action for sharing customer pdf report """
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""
            params = (self.id, self.env.company.id)
            self.env.cr.execute(main_query, params)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount, params)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            report = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
                'base_accounting_kit.res_partner_action', self, data=data)
            data_record = base64.b64encode(report[0])
            ir_values = {
                'name': 'Statement Report',
                'type': 'binary',
                'datas': data_record,
                'mimetype': 'application/pdf',
                'res_model': 'res.partner'
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)
            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached your '
                             'payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')

    def action_print_pdf(self):
        """ Action for printing pdf report """
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""
            params = (self.id, self.env.company.id)
            self.env.cr.execute(main_query, params)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount, params)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return self.env.ref('base_accounting_kit.res_partner_action'
                                ).report_action(self, data=data)
        else:
            raise ValidationError('There is no statement to print')

    def action_print_xlsx(self):
        """ Action for printing xlsx report of customers """
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""
            params = (self.id, self.env.company.id)
            self.env.cr.execute(main_query, params)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount, params)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            return {
                'type': 'ir.actions.report',
                'data': {
                    'model': 'res.partner',
                    'options': json.dumps(data,
                                          default=json_default),
                    'output_format': 'xlsx',
                    'report_name': 'Payment Statement Report'
                },
                'report_type': 'xlsx',
            }
        else:
            raise ValidationError('There is no statement to print')

    def get_xlsx_report(self, data, response):
        """ Get xlsx report data """
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format_with_color = workbook.add_format({
            'font_size': '14px', 'bold': True,
            'bg_color': 'yellow', 'border': 1})
        cell_format = workbook.add_format({'font_size': '14px', 'bold': True})
        txt = workbook.add_format({'font_size': '13px'})
        txt_border = workbook.add_format({'font_size': '13px', 'border': 1})
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '22px'})
        sheet.merge_range('B2:Q4', 'Payment Statement Report', head)
        if data['customer']:
            sheet.merge_range('B7:D7', 'Customer/Supplier : ', cell_format)
            sheet.merge_range('E7:H7', data['customer'], txt)
        sheet.merge_range('B9:C9', 'Address : ', cell_format)
        if data['street']:
            sheet.merge_range('D9:F9', data['street'], txt)
        if data['street2']:
            sheet.merge_range('D10:F10', data['street2'], txt)
        if data['city']:
            sheet.merge_range('D11:F11', data['city'], txt)
        if data['state']:
            sheet.merge_range('D12:F12', data['state'], )
        if data['zip']:
            sheet.merge_range('D13:F13', data['zip'], txt)
        sheet.merge_range('B15:C15', 'Date', cell_format_with_color)
        sheet.merge_range('D15:G15', 'Invoice/Bill Number',
                          cell_format_with_color)
        sheet.merge_range('H15:I15', 'Due Date', cell_format_with_color)
        sheet.merge_range('J15:L15', 'Invoices/Debit', cell_format_with_color)
        sheet.merge_range('M15:O15', 'Amount Due', cell_format_with_color)
        sheet.merge_range('P15:R15', 'Balance Due', cell_format_with_color)
        row = 15
        column = 0
        for record in data['my_data']:
            sub_total = data['currency'] + str(record['sub_total'])
            amount_due = data['currency'] + str(record['amount_due'])
            balance = data['currency'] + str(record['balance'])
            total = data['currency'] + str(data['total'])
            remain_balance = data['currency'] + str(data['balance'])
            sheet.merge_range(row, column + 1, row, column + 2,
                              record['invoice_date'], txt_border)
            sheet.merge_range(row, column + 3, row, column + 6,
                              record['name'], txt_border)
            sheet.merge_range(row, column + 7, row, column + 8,
                              record['invoice_date_due'], txt_border)
            sheet.merge_range(row, column + 9, row, column + 11,
                              sub_total, txt_border)
            sheet.merge_range(row, column + 12, row, column + 14,
                              amount_due, txt_border)
            sheet.merge_range(row, column + 15, row, column + 17,
                              balance, txt_border)
            row = row + 1
        sheet.write(row + 2, column + 1, 'Total Amount: ', cell_format)
        sheet.merge_range(row + 2, column + 3, row + 2, column + 4,
                          total, txt)
        sheet.write(row + 4, column + 1, 'Balance Due: ', cell_format)
        sheet.merge_range(row + 4, column + 3, row + 4, column + 4,
                          remain_balance, txt)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def action_share_xlsx(self):
        """ Action for sharing xlsx report via email """
        if self.customer_report_ids:
            main_query = self.main_query()
            main_query += """ AND move_type IN ('out_invoice')"""
            amount = self.amount_query()
            amount += """ AND move_type IN ('out_invoice')"""
            params = (self.id, self.env.company.id)
            self.env.cr.execute(main_query, params)
            main = self.env.cr.dictfetchall()
            self.env.cr.execute(amount, params)
            amount = self.env.cr.dictfetchall()
            data = {
                'customer': self.display_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'state': self.state_id.name,
                'zip': self.zip,
                'my_data': main,
                'total': amount[0]['total'],
                'balance': amount[0]['balance'],
                'currency': self.currency_id.symbol,
            }
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet()
            cell_format = workbook.add_format({
                'font_size': '14px', 'bold': True})
            txt = workbook.add_format({'font_size': '13px'})
            head = workbook.add_format(
                {'align': 'center', 'bold': True, 'font_size': '22px'})
            sheet.merge_range('B2:P4', 'Payment Statement Report', head)
            date_style = workbook.add_format(
                {'text_wrap': True, 'align': 'center',
                 'num_format': 'yyyy-mm-dd'})
            if data['customer']:
                sheet.write('B7:C7', 'Customer : ', cell_format)
                sheet.merge_range('D7:G7', data['customer'], txt)
            sheet.write('B9:C7', 'Address : ', cell_format)
            if data['street']:
                sheet.merge_range('D9:F9', data['street'], txt)
            if data['street2']:
                sheet.merge_range('D10:F10', data['street2'], txt)
            if data['city']:
                sheet.merge_range('D11:F11', data['city'], txt)
            if data['state']:
                sheet.merge_range('D12:F12', data['state'], txt)
            if data['zip']:
                sheet.merge_range('D13:F13', data['zip'], txt)
            sheet.write('B15', 'Date', cell_format)
            sheet.write('D15', 'Invoice/Bill Number', cell_format)
            sheet.write('H15', 'Due Date', cell_format)
            sheet.write('J15', 'Invoices/Debit', cell_format)
            sheet.write('M15', 'Amount Due', cell_format)
            sheet.write('P15', 'Balance Due', cell_format)
            row = 16
            column = 0
            for record in data['my_data']:
                sub_total = data['currency'] + str(record['sub_total'])
                amount_due = data['currency'] + str(record['amount_due'])
                balance = data['currency'] + str(record['balance'])
                total = data['currency'] + str(data['total'])
                remain_balance = data['currency'] + str(data['balance'])
                sheet.merge_range(row, column + 1, row, column + 2,
                                  record['invoice_date'], date_style)
                sheet.merge_range(row, column + 3, row, column + 5,
                                  record['name'], txt)
                sheet.merge_range(row, column + 7, row, column + 8,
                                  record['invoice_date_due'], date_style)
                sheet.merge_range(row, column + 9, row, column + 10,
                                  sub_total, txt)
                sheet.merge_range(row, column + 12, row, column + 13,
                                  amount_due, txt)
                sheet.merge_range(row, column + 15, row, column + 16,
                                  balance, txt)
                row = row + 1
            sheet.write(row + 2, column + 1, 'Total Amount : ', cell_format)
            sheet.merge_range(row + 2, column + 4, row + 2, column + 5,
                              total, txt)
            sheet.write(row + 4, column + 1, 'Balance Due : ', cell_format)
            sheet.merge_range(row + 4, column + 4, row + 4, column + 5,
                              remain_balance, txt)
            workbook.close()
            output.seek(0)
            xlsx = base64.b64encode(output.read())
            output.close()
            ir_values = {
                'name': "Statement Report.xlsx",
                'type': 'binary',
                'datas': xlsx,
                'store_fname': xlsx,
            }
            attachment = self.env['ir.attachment'].sudo().create(ir_values)
            email_values = {
                'email_to': self.email,
                'subject': 'Payment Statement Report',
                'body_html': '<p>Dear <strong> Mr/Miss. ' + self.name +
                             '</strong> </p> <p> We have attached your'
                             ' payment statement. Please check </p> '
                             '<p>Best regards, </p> <p> ' + self.env.user.name,
                'attachment_ids': [attachment.id],
            }
            mail = self.env['mail.mail'].sudo().create(email_values)
            mail.send()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'Email Sent Successfully',
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError('There is no statement to send')

    # ------------------------------------------------------------------
    # Vendor (supplier) statement — the counterpart to the customer
    # statement above, for posted unpaid vendor bills.
    # ------------------------------------------------------------------
    def _statement_data(self, move_type):
        """Build the statement payload (partner, address, open documents and
        totals) for ``move_type`` — shared by the vendor statement actions."""
        self.ensure_one()
        main_query = self.main_query() + " AND move_type IN ('%s')" % move_type
        amount_query = self.amount_query() + \
            " AND move_type IN ('%s')" % move_type
        params = (self.id, self.env.company.id)
        self.env.cr.execute(main_query, params)
        main = self.env.cr.dictfetchall()
        self.env.cr.execute(amount_query, params)
        amount = self.env.cr.dictfetchall()
        return {
            'customer': self.display_name,
            'street': self.street,
            'street2': self.street2,
            'city': self.city,
            'state': self.state_id.name,
            'zip': self.zip,
            'my_data': main,
            'total': amount[0]['total'],
            'balance': amount[0]['balance'],
            'currency': self.currency_id.symbol,
        }

    def _statement_sent_notification(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Email Sent Successfully',
                'type': 'success',
                'sticky': False,
            },
        }

    def _statement_email_body(self):
        return ('<p>Dear <strong>%s</strong></p>'
                '<p>We have attached your vendor statement. Please check.</p>'
                '<p>Best regards,</p><p>%s</p>' % (
                    self.name, self.env.user.name))

    def action_vendor_print_pdf(self):
        """Print the supplier statement (open vendor bills) as PDF."""
        if not self.vendor_statement_ids:
            raise ValidationError('There is no statement to print')
        data = self._statement_data('in_invoice')
        return self.env.ref(
            'base_accounting_kit.res_partner_action').report_action(
            self, data=data)

    def action_vendor_print_xlsx(self):
        """Export the supplier statement as xlsx."""
        if not self.vendor_statement_ids:
            raise ValidationError('There is no statement to print')
        data = self._statement_data('in_invoice')
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'res.partner',
                'options': json.dumps(data, default=json_default),
                'output_format': 'xlsx',
                'report_name': 'Vendor Statement Report',
            },
            'report_type': 'xlsx',
        }

    def action_vendor_share_pdf(self):
        """Email the supplier statement PDF to the vendor."""
        if not self.vendor_statement_ids:
            raise ValidationError('There is no statement to send')
        data = self._statement_data('in_invoice')
        report = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'base_accounting_kit.res_partner_action', self, data=data)
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Vendor Statement Report',
            'type': 'binary',
            'datas': base64.b64encode(report[0]),
            'mimetype': 'application/pdf',
            'res_model': 'res.partner',
        })
        self.env['mail.mail'].sudo().create({
            'email_to': self.email,
            'subject': 'Vendor Statement Report',
            'body_html': self._statement_email_body(),
            'attachment_ids': [attachment.id],
        }).send()
        return self._statement_sent_notification()

    def action_vendor_share_xlsx(self):
        """Email the supplier statement xlsx to the vendor."""
        if not self.vendor_statement_ids:
            raise ValidationError('There is no statement to send')
        data = self._statement_data('in_invoice')
        # Reuse the customer statement's workbook builder via a stream.
        output = io.BytesIO()
        response = type('XlsxResponse', (object,), {'stream': output})()
        self.get_xlsx_report(data, response)
        output.seek(0)
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'Vendor Statement Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument'
                        '.spreadsheetml.sheet',
            'res_model': 'res.partner',
        })
        output.close()
        self.env['mail.mail'].sudo().create({
            'email_to': self.email,
            'subject': 'Vendor Statement Report',
            'body_html': self._statement_email_body(),
            'attachment_ids': [attachment.id],
        }).send()
        return self._statement_sent_notification()

