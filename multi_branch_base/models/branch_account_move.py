# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    """inherited account move"""
    _inherit = "account.move"

    @api.model
    def _search_default_journal(self, journal_types):
        """methode to set default journal"""
        if len(self.env.user.branch_ids) == 1:
            branch_id = self.env.user.branch_id.id
            domain = [('branch_id', '=', branch_id),
                      ('type', 'in', journal_types)]
            journal = None
            if self._context.get('default_currency_id'):
                currency_domain = domain + [
                    ('currency_id', '=', self._context['default_currency_id'])]
                journal = self.env['account.journal'].search(currency_domain,
                                                             limit=1)
            if not journal:
                journal = self.env['account.journal'].search(domain, limit=1)
            if not journal:
                domain = [('type', 'in', journal_types),
                          ('branch_id', '=', False)]
                journal = self.env['account.journal'].search(domain, limit=1)
            if not journal:
                branch = self.env.user.branch_id
                error_msg = _(
                    "No journal could be found in  %(branch)s branch for "
                    "any of those types: %(journal_types)s",
                    branch=branch.name,
                    journal_types=', '.join(journal_types),
                )
                raise UserError(error_msg)
            return journal
        else:
            company_id = self.company_id.id if self.company_id else self._context.get('default_company_id',
                                           self.env.company.id)

            domain = [('company_id', '=', company_id),
                      ('type', 'in', journal_types)]
            journal = None
            if self._context.get('default_currency_id'):
                currency_domain = domain + [
                    ('currency_id', '=', self._context['default_currency_id'])]
                journal = self.env['account.journal'].search(currency_domain,
                                                             limit=1)
            if not journal:
                journal = self.env['account.journal'].search(domain, limit=1)
            if not journal:
                company = self.env['res.company'].browse(company_id)
                error_msg = _(
                    "No journal could be found in company %(company_name)s for "
                    "any of those types: %(journal_types)s",
                    company_name=company.display_name,
                    journal_types=', '.join(journal_types),
                )
                raise UserError(error_msg)

            return journal

    def _get_default_branch(self):
        branch = False
        if len(self.env.user.branch_ids) == 1:
            branch = self.env.user.branch_id
            return branch

    def _get_branch_domain(self):
        """methode to get branch domain"""
        company = self.env.company
        branch_ids = self.env.user.branch_ids
        branch = branch_ids.filtered(
            lambda branch: branch.company_id == company)
        return [('id', 'in', branch.ids)]

    branch_id = fields.Many2one('res.branch', string='Branch', store=True,
                                readonly=False,
                                default=_get_default_branch,
                                domain=_get_branch_domain)

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        """onchange methode"""
        move_type = self._context.get('default_move_type', 'entry')
        if move_type in self.get_sale_types(include_receipts=True):
            journal_types = ['sale']
        elif move_type in self.get_purchase_types(include_receipts=True):
            journal_types = ['purchase']
        else:
            journal_types = self._context.get('default_move_journal_types', ['general'])
        branch_id = self.branch_id.id
        domain = [('branch_id', '=', branch_id),
                  ('type', 'in', journal_types)]
        journal = None
        if self._context.get('default_currency_id'):
            currency_domain = domain + [
                ('currency_id', '=', self._context['default_currency_id'])]
            journal = self.env['account.journal'].search(currency_domain,
                                                         limit=1)
        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)
        if not journal:
            domain = [('type', 'in', journal_types),
                      ('branch_id', '=', False)]
            journal = self.env['account.journal'].search(domain, limit=1)
        if not journal and journal_types:
            branch = self.branch_id
            error_msg = _(
                "No journal could be found in %(branch)s branch for "
                "any of those types: %(journal_types)s",
                branch=branch.name,
                journal_types=', '.join(journal_types),
            )
            raise UserError(error_msg)
        self.journal_id = journal

    @api.depends('company_id', 'invoice_filter_type_domain')
    def _compute_suitable_journal_ids(self):
        """methode to compute suitable journal ids"""
        if self.branch_id:
            for m in self:
                journal_type = m.invoice_filter_type_domain or 'general'
                branch_id = m.branch_id.id #or self.env.user.branch_id.id
                domain = [('type', '=', journal_type),
                          '|', ('branch_id', '=', branch_id),
                          ('branch_id', '=', False)]
                m.suitable_journal_ids = self.env['account.journal'].search(
                    domain)

        else:
            for m in self:
                journal_type = m.invoice_filter_type_domain or 'general'
                company_id = m.company_id.id if m.company_id else self.env.company.id
                domain = [('company_id', '=', company_id),
                          ('branch_id', '=', False),
                          ('type', '=', journal_type)]
                m.suitable_journal_ids = self.env['account.journal'].search(
                    domain)

    @api.constrains('branch_id', 'line_ids')
    def _check_move_line_branch_id(self):
        """methode to check branch of accounts and entry"""
        for move in self:
            branches = move.line_ids.account_id.branch_id
            if branches and branches != move.branch_id:
                bad_accounts = move.line_ids.account_id.filtered(
                    lambda a: a.branch_id and a.branch_id != move.branch_id)
                raise ValidationError(_(
                    "Your items contains accounts from %(line_branch)s branch"
                    " whereas your entry belongs to %(move_branch)s branch. "
                    "\n Please change the branch of your entry or remove the "
                    "accounts from other branches (%(bad_accounts)s).",
                    line_branch=', '.join(branches.mapped('name')),
                    move_branch=move.branch_id.name,
                    bad_accounts=', '.join(bad_accounts.mapped('name')),
                ))


class AccountMoveLine(models.Model):
    """inherited account move line"""
    _inherit = "account.move.line"

    branch_id = fields.Many2one('res.branch', related='move_id.branch_id',
                                string='Branch', store=True)

    account_id = fields.Many2one(
        'account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False), ('company_id', '=', 'company_id'),"
               "('is_off_balance', '=', False), '|', "
               "('branch_id', '=', branch_id), ('branch_id', '=', False)]",
        check_company=True,
        tracking=True)
