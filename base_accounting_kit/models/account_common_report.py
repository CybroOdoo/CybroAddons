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
from odoo import api, fields, models
from odoo.tools import get_lang


class AccountCommonReport(models.TransientModel):
    """Base wizard for the accounting reports of this module.

    In Odoo 19 ``account.report`` is the core declarative reporting engine
    model, so the report wizards can no longer inherit it. This transient
    model reintroduces the shared filter fields and helpers (previously
    provided by the removed core ``account.common.report``) that the report
    wizards rely on."""
    _name = "account.common.report"
    _description = "Account Common Report"
    _inherit = "account.report.xlsx.mixin"

    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, readonly=True,
                                 default=lambda self: self.env.company)
    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Journals',
        required=True,
        default=lambda self: self.env['account.journal'].search(
            [('company_id', '=', self.company_id.id)]),
        domain="[('company_id', '=', company_id)]")
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves',
                                   required=True, default='posted')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Onchange function based on the company and updated the journals"""
        if self.company_id:
            self.journal_ids = self.env['account.journal'].search(
                [('company_id', '=', self.company_id.id)])
        else:
            self.journal_ids = self.env['account.journal'].search([])

    def _build_contexts(self, data):
        """Builds the context information for the given data"""
        result = {}
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form'][
            'journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form'][
            'target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
        result['company_id'] = data['form']['company_id'][0] or False
        return result

    def _print_report(self, data):
        """Raise an error if the report comes checked """
        raise NotImplementedError()

    def action_print_xlsx(self):
        """Export the report to xlsx. Implemented by each concrete wizard;
        declared here so the shared report form validates the button."""
        raise NotImplementedError()

    def check_report(self):
        """Function to check if the report comes active models and related
        values"""
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'date_to', 'journal_ids', 'target_move',
             'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                             lang=get_lang(self.env).code)
        return self.with_context(discard_logo_check=True)._print_report(data)

    # ------------------------------------------------------------------
    # XLSX export
    #
    # A small generic engine shared by every report wizard. A wizard's
    # ``action_print_xlsx`` builds a normalised ``table`` dict and returns
    # ``self._xlsx_action(...)``. ``action_manager.js`` turns the returned
    # action into a POST to the ``/xlsx_report`` controller, which calls
    # ``get_xlsx_report`` (below) to stream the workbook.
    #
    # ``table`` shape::
    #     {
    #       'title': str,
    #       'meta': [[label, value], ...],
    #       'columns': [{'label': str, 'width': int, 'num': bool}, ...],
    #       'rows': [{'cells': [...], 'bold': bool, 'indent': int}, ...],
    #     }
    # ------------------------------------------------------------------
    def _xlsx_base_data(self):
        """Build the shared ``data`` dict (mirrors ``check_report``) so a
        wizard's xlsx export reuses the exact same filters as its PDF."""
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'date_to', 'journal_ids', 'target_move',
             'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context,
                                             lang=get_lang(self.env).code)
        return data

    def _period_account_balances(self, accounts, date_from, date_to):
        """Return ``{account_id: balance}`` over an explicit date range,
        honouring the wizard's target-move / company / journal filters. Used
        by the report comparison columns."""
        ctx = {
            'date_from': date_from,
            'date_to': date_to,
            'strict_range': bool(date_from),
            'state': self.target_move,
            'company_id': self.company_id.id,
            'journal_ids': self.journal_ids.ids,
        }
        aml = self.env['account.move.line'].with_context(ctx)
        tables, where_clause, where_params = aml._query_get()
        tables = tables.replace('"', '') if tables else 'account_move_line'
        where = ' AND ' + where_clause if where_clause.strip() else ''
        query = ("SELECT account_id, "
                 "COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0) AS balance"
                 " FROM " + tables + " WHERE account_id IN %s" + where +
                 " GROUP BY account_id")
        self.env.cr.execute(query,
                            (tuple(accounts.ids),) + tuple(where_params))
        return {r['account_id']: r['balance']
                for r in self.env.cr.dictfetchall()}
