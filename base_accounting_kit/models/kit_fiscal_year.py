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
from odoo.exceptions import UserError, ValidationError


class KitFiscalYear(models.Model):
    """Fiscal years of a company (P2.3-b). Dates covered by a record use it
    everywhere core asks for the fiscal year (``res.company.
    compute_fiscalyear_dates``: report periods, opening balances, sequence
    ranges); other dates follow the company's Fiscal Year Last Day.
    Closing a year sets the Global Lock Date to its end."""
    _name = 'kit.fiscal.year'
    _description = 'Fiscal Year'
    _inherit = ['mail.thread']
    _order = 'date_from desc'
    _check_company_auto = True

    name = fields.Char(
        string="Name", compute='_compute_name', store=True, readonly=False,
        precompute=True,
        required=True, tracking=True)
    date_from = fields.Date(string="Start Date", required=True, tracking=True)
    date_to = fields.Date(string="End Date", required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string="Company", required=True,
        default=lambda self: self.env.company.root_id,
        domain="[('parent_id', '=', False)]",
        help="Fiscal years are kept on the main company; its branches "
             "follow them.")
    state = fields.Selection(
        [('open', 'Open'), ('closed', 'Closed')], string="Status",
        default='open', required=True, readonly=True, copy=False,
        tracking=True)
    closing_move_id = fields.Many2one(
        'account.move', string="Closing Entry", readonly=True, copy=False,
        help="Year-end entry moving the result to Retained Earnings.")
    lock_date_before = fields.Date(
        string="Global Lock Date before Closing", readonly=True, copy=False,
        help="Restored when the year is reopened.")

    _date_order = models.Constraint(
        'CHECK (date_from <= date_to)',
        'The end date of a fiscal year must be after its start date.')

    @api.depends('date_from', 'date_to')
    def _compute_name(self):
        for year in self:
            if not year.name and year.date_from and year.date_to:
                year.name = _("FY %s", year.date_from.year) \
                    if year.date_from.year == year.date_to.year \
                    else _("FY %(start)s-%(end)s", start=year.date_from.year,
                           end=year.date_to.strftime('%y'))

    @api.constrains('date_from', 'date_to', 'company_id')
    def _check_dates(self):
        for year in self:
            if (year.date_to - year.date_from).days > 731:
                raise ValidationError(_(
                    "A fiscal year cannot be longer than 24 months."))
            overlap = self.search([
                ('id', '!=', year.id),
                ('company_id', '=', year.company_id.id),
                ('date_from', '<=', year.date_to),
                ('date_to', '>=', year.date_from)], limit=1)
            if overlap:
                raise ValidationError(_(
                    "%(year)s overlaps %(other)s (%(start)s - %(end)s).",
                    year=year.name, other=overlap.name,
                    start=overlap.date_from, end=overlap.date_to))

    def write(self, vals):
        if {'date_from', 'date_to', 'company_id'} & set(vals) and \
                self.filtered(lambda y: y.state == 'closed'):
            raise UserError(_("Reopen the fiscal year before changing its "
                              "dates."))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_closed(self):
        if self.filtered(lambda y: y.state == 'closed'):
            raise UserError(_("A closed fiscal year cannot be deleted."))

    # ------------------------------------------------------------------
    def _check_chief(self):
        if not (self.env.user.has_group('base_accounting_kit.group_account_chief')
                or self.env.su):
            raise UserError(_("Only Chief Accountants can close or reopen "
                              "fiscal years."))

    def action_close(self):
        """Close Year: opens the Year-end Closing wizard (checks, closing
        entry, then ``_close``)."""
        self.ensure_one()
        self._check_chief()
        return {'type': 'ir.actions.act_window', 'res_model': 'kit.year.closing',
                'name': _("Year-end Closing %s", self.name),
                'views': [(False, 'form')], 'target': 'new',
                'context': {'default_fiscal_year_id': self.id}}

    def _close(self, closing_move=None):
        """Close the year: every earlier year must be closed; the Global
        Lock Date moves to the year's end (core checks it, e.g. bank
        transactions still to reconcile)."""
        self._check_chief()
        for year in self.filtered(lambda y: y.state == 'open').sorted('date_from'):
            earlier = self.search([('company_id', '=', year.company_id.id),
                                   ('state', '=', 'open'),
                                   ('date_to', '<', year.date_from)],
                                  order='date_from', limit=1)
            if earlier:
                raise UserError(_("Close %s first: fiscal years are closed "
                                  "in order.", earlier.name))
            company = year.company_id.sudo()
            lock = company.fiscalyear_lock_date
            year.write({'lock_date_before': lock,
                        'closing_move_id': closing_move.id if closing_move else False})
            if not lock or lock < year.date_to:
                company.write({'fiscalyear_lock_date': year.date_to})
            year.state = 'closed'
            year.message_post(body=_("Fiscal year closed; Global Lock Date "
                                     "%s.", company.fiscalyear_lock_date))
        return True

    def action_reopen(self):
        """Reopen the last closed year: give back the Global Lock Date it
        had before closing and reverse its closing entry. Not possible
        under the Hard Lock Date."""
        self._check_chief()
        for year in self.filtered(lambda y: y.state == 'closed'):
            later = self.search([('company_id', '=', year.company_id.id),
                                 ('state', '=', 'closed'),
                                 ('date_from', '>', year.date_to)], limit=1)
            if later:
                raise UserError(_("Reopen %s first: only the last closed "
                                  "fiscal year can be reopened.", later.name))
            company = year.company_id.sudo()
            if company.hard_lock_date and company.hard_lock_date >= year.date_from:
                raise UserError(_(
                    "The Hard Lock Date (%s) covers this fiscal year. It is "
                    "final, so the year cannot be reopened.",
                    company.hard_lock_date))
            lock = company.fiscalyear_lock_date
            if lock and lock > year.date_to:
                raise UserError(_(
                    "The Global Lock Date (%s) is after this fiscal year. "
                    "Move it back in Lock Dates first.", lock))
            if lock == year.date_to:
                company.write({'fiscalyear_lock_date': year.lock_date_before})
            if year.closing_move_id.state == 'posted':
                # reversed (not deleted): the history stays visible
                year.closing_move_id._reverse_moves([{
                    'date': year.closing_move_id.date,
                    'ref': _("Reopen %s", year.name)}], cancel=True)
            year.write({'state': 'open', 'lock_date_before': False,
                        'closing_move_id': False})
            year.message_post(body=_("Fiscal year reopened; Global Lock Date "
                                     "%s.", company.fiscalyear_lock_date
                                     or _("none")))
        return True

    def action_open_closing_move(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'account.move',
                'res_id': self.closing_move_id.id, 'views': [(False, 'form')],
                'target': 'current'}

    def action_create_next_year(self):
        """List button: the 12 months after the last year of the company,
        or the year of today (company setting) when there is none."""
        company = self.env.company.root_id
        last = self.search([('company_id', '=', company.id)],
                           order='date_to desc', limit=1)
        if last:
            date_from = last.date_to + timedelta(days=1)
            date_to = date_from + relativedelta(years=1, days=-1)
        else:
            dates = company.compute_fiscalyear_dates(
                fields.Date.context_today(self))
            date_from, date_to = dates['date_from'], dates['date_to']
        year = self.create({'company_id': company.id, 'date_from': date_from,
                            'date_to': date_to})
        return {'type': 'ir.actions.act_window', 'res_model': self._name,
                'res_id': year.id, 'views': [(False, 'form')],
                'target': 'current'}
