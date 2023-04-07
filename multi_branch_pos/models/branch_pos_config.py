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

"""pos config"""

from odoo import fields, models, api


class PointOfSaleBranch(models.Model):
    """inherit pos config to add new branch field"""
    _inherit = 'pos.config'

    branch_id = fields.Many2one('res.branch', string='Branch', store=True,
                                readonly=False, compute='_compute_branch')
    branch_name = fields.Char(string="Branch Name", store=True,
                              related='branch_id.name')
    email = fields.Char(related='branch_id.email', store=True)
    phone = fields.Char(related='branch_id.phone', store=True)
    website = fields.Char(related='branch_id.website', store=True)
    allowed_branch_ids = fields.Many2many('res.branch', store=True,
                                          string="Allowed Branches",
                                          compute='_compute_allowed_branch_ids')

    @api.depends('company_id')
    def _compute_allowed_branch_ids(self):
        for pos in self:
            pos.allowed_branch_ids = self.env.user.branch_ids.ids

    @api.depends('company_id')
    def _compute_branch(self):
        for order in self:
            pos_company = order.company_id if order.company_id else self.env.company
            branch_ids = self.env.user.branch_ids
            branch = branch_ids.filtered(
                lambda branch: branch.company_id == pos_company)
            if branch:
                order.branch_id = branch.ids[0]
            else:
                order.branch_id = False

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        for pos in self:
            if pos.branch_id:
                picking = self.env['stock.warehouse'].search(
                    [('branch_id', '=', self.env.user.branch_id.id),
                     ('company_id', '=', self.env.company.id)],
                    limit=1)
                if not picking:
                    picking = self.env['stock.warehouse'].search(
                        [('branch_id', '=', False),
                         ('company_id', '=', self.env.company.id)],
                        limit=1)
                sales_journal = self.env['account.journal'].search(
                    [('type', '=', 'sale'),
                     ('company_id', '=', self.env.company.id),
                     ('branch_id', '=', self.env.user.branch_id.id),
                     ('code', 'ilike', 'POSS')], limit=1)
                print(sales_journal)
                if not sales_journal:
                    sales_journal = self.env['account.journal'].search(
                        [('type', '=', 'sale'),
                         ('company_id', '=', self.env.company.id),
                         ('branch_id', '=', False),
                         ('code', 'ilike', 'POSS')], limit=1)
                invoice_journal = self.env['account.journal'].search(
                    [('type', '=', 'sale'),
                     ('company_id', '=', self.env.company.id),
                     ('branch_id', '=', self.env.user.branch_id.id)], limit=1)
                if not invoice_journal:
                    invoice_journal = self.env['account.journal'].search(
                        [('type', '=', 'sale'),
                         ('company_id', '=', self.env.company.id),
                         ('branch_id', '=', False)], limit=1)
            else:
                picking = self.env['stock.warehouse'].search(
                    [('company_id', '=', self.env.company.id)],
                    limit=1)
                sales_journal = self.env['account.journal'].search([
                    ('type', '=', 'sale'),
                    ('company_id', '=', self.env.company.id),
                    ('code', '=', 'POSS')], limit=1)
                invoice_journal = self.env['account.journal'].search(
                    [('type', '=', 'sale'),
                     ('company_id', '=', self.env.company.id)], limit=1)
            self.picking_type_id = picking.pos_type_id.id
            self.journal_id = sales_journal.id
            self.invoice_journal_id = invoice_journal.id

    def _default_picking_type_id(self):
        """methode to set default picking type"""
        if self.env.user.branch_id:
            picking = self.env['stock.warehouse'].search(
                [('branch_id', '=', self.env.user.branch_id.id),
                 ('company_id', '=', self.env.company.id)],
                limit=1)
            if not picking:
                picking = self.env['stock.warehouse'].search(
                    [('branch_id', '=', False),
                     ('company_id', '=', self.env.company.id)],
                    limit=1)
            return picking.pos_type_id.id
        return self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1).pos_type_id.id

    def _default_sale_journal(self):
        """methode to set default sale journal"""
        if self.env.user.branch_id:
            sales_journal = self.env['account.journal'].search(
                [('type', '=', 'sale'),
                 ('company_id', '=', self.env.company.id),
                 ('branch_id', '=', self.env.user.branch_id.id),
                 ('code', 'ilike', 'POSS')], limit=1)
            if not sales_journal:
                sales_journal = self.env['account.journal'].search(
                    [('type', '=', 'sale'),
                     ('company_id', '=', self.env.company.id),
                     ('branch_id', '=', False),
                     ('code', 'ilike', 'POSS')], limit=1)
            return sales_journal
        return self.env['account.journal'].search([
            ('type', '=', 'sale'), ('company_id', '=', self.env.company.id),
            ('code', '=', 'POSS')], limit=1)

    def _default_invoice_journal(self):
        """methode to set default invoice journal"""
        if self.env.user.branch_id:
            invoice_journal = self.env['account.journal'].search(
                [('type', '=', 'sale'),
                 ('company_id', '=', self.env.company.id),
                 ('branch_id', '=', self.env.user.branch_id.id)], limit=1)
            if not invoice_journal:
                invoice_journal = self.env['account.journal'].search(
                    [('type', '=', 'sale'),
                     ('company_id', '=', self.env.company.id),
                     ('branch_id', '=', False)], limit=1)
            return invoice_journal
        return self.env['account.journal'].search(
            [('type', '=', 'sale'),
             ('company_id', '=', self.env.company.id)], limit=1)

    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Operation Type',
        default=_default_picking_type_id,
        required=True,
        domain="[('code', '=', 'outgoing'), "
               "'|', ('warehouse_id.branch_id', '=', branch_id),"
               " ('warehouse_id.branch_id', '=', False)]",
        ondelete='restrict')
    journal_id = fields.Many2one(
        'account.journal', string='Sales Journal',
        domain=[('type', '=', 'sale')],
        help="Accounting journal used to post sales entries.",
        default=_default_sale_journal,
        ondelete='restrict')
    invoice_journal_id = fields.Many2one(
        'account.journal', string='Invoice Journal',
        domain=[('type', '=', 'sale')],
        help="Accounting journal used to create invoices.",
        default=_default_invoice_journal)
