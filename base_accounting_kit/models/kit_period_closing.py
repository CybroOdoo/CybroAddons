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
from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import date_utils


class KitClosingTaskTemplate(models.Model):
    """Tasks copied into every new month-end closing (P2.3-d)."""
    _name = 'kit.closing.task.template'
    _description = 'Closing Task Template'
    _order = 'sequence, id'

    name = fields.Char(string="Task", required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string="Responsible",
                              domain="[('share', '=', False)]")
    due_day = fields.Integer(
        string="Due Day", default=5,
        help="Day of the following month the task is due (1-28).")
    note = fields.Text(string="Notes", translate=True)
    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self.env.company.root_id,
        domain="[('parent_id', '=', False)]")

    _due_day_range = models.Constraint(
        'CHECK (due_day BETWEEN 1 AND 28)',
        'The due day must be between 1 and 28.')


class KitPeriodClosing(models.Model):
    """Month-end closing of a company (P2.3-d): automatic checks computed
    from core data, the month's tasks with responsible people, then Close
    (optionally setting the Global Lock Date to the month end)."""
    _name = 'kit.period.closing'
    _description = 'Month-end Closing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_from desc'
    _mail_post_access = 'read'

    name = fields.Char(compute='_compute_name', store=True, precompute=True,
                       readonly=False, required=True)
    date_from = fields.Date(string="Start Date", required=True, readonly=True)
    date_to = fields.Date(string="End Date", required=True, readonly=True)
    company_id = fields.Many2one(
        'res.company', string="Company", required=True, readonly=True,
        default=lambda self: self.env.company.root_id)
    currency_id = fields.Many2one(related='company_id.currency_id')
    state = fields.Selection([('open', 'Open'), ('closed', 'Closed')],
                             string="Status", default='open', required=True,
                             readonly=True, copy=False, tracking=True)
    task_ids = fields.One2many('kit.period.closing.task', 'closing_id',
                               string="Tasks")
    progress = fields.Float(compute='_compute_progress', string="Progress")
    lock_month = fields.Boolean(
        string="Lock the month", default=True,
        groups='base_accounting_kit.group_account_chief',
        help="Closing sets the Global Lock Date to the end of the month.")
    close_anyway = fields.Boolean(
        string="Close anyway", groups='base_accounting_kit.group_account_chief',
        help="Close although some checks show warnings.")
    lock_date_before = fields.Date(readonly=True, copy=False)

    draft_count = fields.Integer(compute='_compute_checks')
    unreconciled_count = fields.Integer(compute='_compute_checks')
    transit_count = fields.Integer(compute='_compute_checks')
    transit_amount = fields.Monetary(compute='_compute_checks',
                                     string="In Transit")
    negative_bank_count = fields.Integer(compute='_compute_checks')
    duplicate_bill_count = fields.Integer(compute='_compute_checks')
    depreciation_count = fields.Integer(compute='_compute_checks')
    has_blocking = fields.Boolean(compute='_compute_checks')
    has_warnings = fields.Boolean(compute='_compute_checks')

    _month_unique = models.Constraint(
        'unique (company_id, date_from)',
        'This month already has a closing.')

    @api.depends('date_from')
    def _compute_name(self):
        for closing in self:
            if not closing.name and closing.date_from:
                closing.name = closing.date_from.strftime('%b %Y')

    @api.depends('task_ids.done')
    def _compute_progress(self):
        for closing in self:
            tasks = closing.task_ids
            closing.progress = 100.0 * len(tasks.filtered('done')) / len(tasks) if tasks else 100.0

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    def _companies(self):
        return self.env['res.company'].search(
            [('id', 'child_of', self.company_id.ids)])

    def _transit_accounts(self):
        """Outstanding receipts / payments accounts of the bank and cash
        journals and the internal transfer account."""
        journals = self.env['account.journal'].search([
            ('company_id', 'in', self._companies().ids), ('type', 'in', ('bank', 'cash'))])
        lines = journals.inbound_payment_method_line_ids | journals.outbound_payment_method_line_ids
        return (lines.payment_account_id | self.company_id.transfer_account_id).filtered('reconcile')

    def _negative_journals(self):
        journals = self.env['account.journal'].search([
            ('company_id', 'in', self._companies().ids), ('type', 'in', ('bank', 'cash')),
            ('default_account_id', '!=', False)])
        balances = dict(self.env['account.move.line']._read_group([
            ('account_id', 'in', journals.default_account_id.ids),
            ('parent_state', '=', 'posted'), ('date', '<=', self.date_to),
            ('company_id', 'in', self._companies().ids)],
            ['account_id'], ['balance:sum']))
        return journals.filtered(lambda j: self.currency_id.compare_amounts(
            balances.get(j.default_account_id, 0.0), 0.0) < 0)

    def _duplicate_bills(self):
        bills = self.env['account.move'].search([
            ('company_id', 'in', self._companies().ids),
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('state', '!=', 'cancel'), ('date', '>=', self.date_from),
            ('date', '<=', self.date_to)])
        return bills.filtered('duplicated_ref_ids')

    def _check_domains(self):
        """Model and domain of each check (counts and Open buttons)."""
        self.ensure_one()
        companies = self._companies().ids
        return {
            'draft': ('account.move', [
                ('company_id', 'in', companies), ('state', '=', 'draft'),
                ('date', '>=', self.date_from), ('date', '<=', self.date_to)]),
            'unreconciled': ('account.bank.statement.line',
                             self.company_id._get_unreconciled_statement_lines_domain(self.date_to)),
            'transit': ('account.move.line', [
                ('company_id', 'in', companies), ('account_id', 'in', self._transit_accounts().ids),
                ('reconciled', '=', False), ('parent_state', '=', 'posted'),
                ('date', '<=', self.date_to)]),
            'negative_bank': ('account.journal', [('id', 'in', self._negative_journals().ids)]),
            'duplicate_bill': ('account.move', [('id', 'in', self._duplicate_bills().ids)]),
            'depreciation': ('account.asset.depreciation.line', [
                ('asset_id.company_id', 'in', companies), ('asset_id.state', '=', 'open'),
                ('move_id', '=', False), ('depreciation_date', '<=', self.date_to)]),
        }

    @api.depends('date_from', 'date_to', 'lock_month', 'state')
    def _compute_checks(self):
        for closing in self:
            counts, amount = {}, 0.0
            if closing.date_from and closing.state == 'open':
                for key, (model, domain) in closing._check_domains().items():
                    counts[key] = self.env[model].search_count(domain)
                amount = sum(self.env['account.move.line'].search(
                    closing._check_domains()['transit'][1]).mapped('amount_residual'))
            for key in ('draft', 'unreconciled', 'transit', 'negative_bank',
                        'duplicate_bill', 'depreciation'):
                closing['%s_count' % key] = counts.get(key, 0)
            closing.transit_amount = amount
            closing.has_blocking = bool(closing.lock_month and closing.unreconciled_count)
            closing.has_warnings = bool(
                closing.draft_count or closing.transit_count or closing.negative_bank_count
                or closing.duplicate_bill_count or closing.depreciation_count
                or (closing.unreconciled_count and not closing.lock_month))

    def action_open_check(self):
        self.ensure_one()
        model, domain = self._check_domains()[self.env.context['check']]
        return {'type': 'ir.actions.act_window', 'res_model': model,
                'name': self.env[model]._description, 'domain': domain,
                'views': [(False, 'list'), (False, 'form')], 'target': 'current'}

    # ------------------------------------------------------------------
    # Months and tasks
    # ------------------------------------------------------------------
    @api.model
    def _start_month(self, company, month_start):
        """The closing of a month with the company's task templates; a
        To-Do activity for each responsible person."""
        date_to = date_utils.end_of(month_start, 'month')
        closing = self.create({'company_id': company.id, 'date_from': month_start,
                               'date_to': date_to})
        templates = self.env['kit.closing.task.template'].search(
            [('company_id', '=', company.id)])
        next_month = date_to + timedelta(days=1)
        closing.task_ids = [fields.Command.create({
            'name': template.name, 'sequence': template.sequence,
            'user_id': template.user_id.id, 'note': template.note,
            'date_deadline': next_month.replace(day=template.due_day)})
            for template in templates]
        return closing

    def action_create_next_month(self):
        """List button: the month after the last closing of the company, or
        last month when there is none."""
        self._check_chief()
        company = self.env.company.root_id
        last = self.search([('company_id', '=', company.id)], order='date_from desc', limit=1)
        today = fields.Date.context_today(self)
        start = last.date_to + timedelta(days=1) if last else \
            date_utils.start_of(today - relativedelta(months=1), 'month')
        closing = self._start_month(company, start)
        return {'type': 'ir.actions.act_window', 'res_model': self._name,
                'res_id': closing.id, 'views': [(False, 'form')], 'target': 'current'}

    # ------------------------------------------------------------------
    # Close / reopen
    # ------------------------------------------------------------------
    def _check_chief(self):
        if not (self.env.user.has_group('base_accounting_kit.group_account_chief')
                or self.env.su):
            raise UserError(_("Only Chief Accountants can start, close or "
                              "reopen month-end closings."))

    def action_close(self):
        self._check_chief()
        for closing in self.filtered(lambda c: c.state == 'open'):
            open_tasks = closing.task_ids.filtered(lambda t: not t.done)
            if open_tasks:
                raise UserError(_("Some tasks are not done yet: %s",
                                  ', '.join(open_tasks.mapped('name'))))
            if closing.has_blocking:
                raise UserError(_("Reconcile the bank transactions up to the "
                                  "end of the month first (or close without "
                                  "locking the month)."))
            if closing.has_warnings and not closing.close_anyway:
                raise UserError(_("Some checks are not passed. Solve them or "
                                  "tick \"Close anyway\"."))
            company = closing.company_id.sudo()
            closing.lock_date_before = company.fiscalyear_lock_date
            if closing.lock_month and (not company.fiscalyear_lock_date
                                       or company.fiscalyear_lock_date < closing.date_to):
                company.write({'fiscalyear_lock_date': closing.date_to})
            closing.state = 'closed'
            closing.message_post(body=_("Month closed; Global Lock Date %s.",
                                        company.fiscalyear_lock_date or _("none")))
        return True

    def action_reopen(self):
        self._check_chief()
        for closing in self.filtered(lambda c: c.state == 'closed'):
            # only the most recent closed month of the company can reopen
            last = self.search([('state', '=', 'closed'),
                                ('company_id', '=', closing.company_id.id)],
                               order='date_to desc', limit=1)
            later = last if last.date_to > closing.date_to else self.browse()
            if later:
                raise UserError(_("Reopen %s first: only the last closed month "
                                  "can be reopened.", later.name))
            company = closing.company_id.sudo()
            if company.hard_lock_date and company.hard_lock_date >= closing.date_from:
                raise UserError(_("The Hard Lock Date (%s) covers this month. It "
                                  "is final, so the month cannot be reopened.",
                                  company.hard_lock_date))
            lock = company.fiscalyear_lock_date
            if lock and lock > closing.date_to:
                raise UserError(_("The Global Lock Date (%s) is after this month. "
                                  "Move it back in Lock Dates first.", lock))
            if lock == closing.date_to and closing.lock_month:
                company.write({'fiscalyear_lock_date': closing.lock_date_before})
            closing.write({'state': 'open', 'lock_date_before': False,
                           'close_anyway': False})
            closing.message_post(body=_("Month reopened; Global Lock Date %s.",
                                        company.fiscalyear_lock_date or _("none")))
        return True


class KitPeriodClosingTask(models.Model):
    """A task of a month-end closing; Done records who and when and closes
    the responsible person's activity."""
    _name = 'kit.period.closing.task'
    _description = 'Month-end Closing Task'
    _order = 'sequence, id'

    closing_id = fields.Many2one('kit.period.closing', required=True,
                                 ondelete='cascade', index=True)
    company_id = fields.Many2one(related='closing_id.company_id', store=True)
    name = fields.Char(string="Task", required=True)
    sequence = fields.Integer(default=10)
    user_id = fields.Many2one('res.users', string="Responsible",
                              domain="[('share', '=', False)]")
    date_deadline = fields.Date(string="Due")
    note = fields.Text(string="Notes")
    done = fields.Boolean(readonly=True, copy=False)
    done_uid = fields.Many2one('res.users', string="Done by", readonly=True, copy=False)
    done_date = fields.Datetime(string="Done on", readonly=True, copy=False)
    activity_id = fields.Many2one('mail.activity', readonly=True, copy=False,
                                  ondelete='set null')

    def _check_open(self):
        if self.closing_id.filtered(lambda c: c.state == 'closed'):
            raise UserError(_("Reopen the month to change its tasks."))

    def _schedule_activity(self):
        for task in self.filtered(lambda t: t.user_id and not t.done and not t.activity_id):
            task.activity_id = task.closing_id.sudo().activity_schedule(
                'mail.mail_activity_data_todo', date_deadline=task.date_deadline,
                summary=task.name, note=task.note, user_id=task.user_id.id)

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        tasks._check_open()
        tasks._schedule_activity()
        return tasks

    def action_done(self):
        self._check_open()
        for task in self.filtered(lambda t: not t.done):
            task.write({'done': True, 'done_uid': self.env.uid,
                        'done_date': fields.Datetime.now()})
            if task.activity_id:
                activity, task.activity_id = task.activity_id, False
                # core may archive the done activity (keep done) or delete it
                activity.sudo().action_feedback(feedback=_("Done"))
            task.closing_id.message_post(body=_("Task done: %s", task.name))
        return True

    def action_undo(self):
        self._check_open()
        self.write({'done': False, 'done_uid': False, 'done_date': False})
        self._schedule_activity()
        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_except_closed(self):
        self._check_open()
        self.activity_id.sudo().unlink()
