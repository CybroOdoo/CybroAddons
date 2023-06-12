# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana J(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""pos config"""
from odoo import api, fields, models


class PointOfSaleBranch(models.Model):
    """inherit pos config to add new branch field"""
    _inherit = 'pos.config'

    def _default_picking_type_id(self):
        """function to set default picking type"""
        domain = [('company_id', '=', self.env.company.id)]
        if self.env.user.branch_id:
            domain += ['|', ('branch_id', '=', False),
                       ('branch_id', '=', self.env.user.branch_id.id)]
        else:
            domain += [('branch_id', '=', False)]
        warehouse = self.env['stock.warehouse'].search(domain, limit=1)
        return warehouse.pos_type_id.id if warehouse else False

    def _default_sale_journal(self):
        """function to set default sale journal"""
        if self.env.user.branch_id:
            sales_journal = self.env['account.journal'].search(
                [('type', 'in', ('sale', 'general')),
                 ('company_id', '=', self.env.company.id),
                 ('branch_id', '=', self.env.user.branch_id.id),
                 ('code', 'ilike', 'POSS')], limit=1)
            if not sales_journal:
                sales_journal = self.env['account.journal'].search(
                    [('type', 'in', ('sale', 'general')),
                     ('company_id', '=', self.env.company.id),
                     ('branch_id', '=', False),
                     ('code', 'ilike', 'POSS')], limit=1)
            return sales_journal
        return self.env['account.journal'].search([
            ('type', 'in', ('sale', 'general')), ('company_id', '=',
                                                  self.env.company.id),
            ('code', '=', 'POSS')], limit=1)

    def _default_invoice_journal(self):
        """function to set default invoice journal"""
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

    branch_id = fields.Many2one('res.branch', string='Branch', store=True,
                                readonly=False, compute='_compute_branch',
                                help='Branches allowed')
    branch_name = fields.Char(string="Branch Name", store=True,
                              help='Branch name',
                              related='branch_id.name')
    email = fields.Char(related='branch_id.email', string="Email",
                        help='Email of specific branch', store=True)
    phone = fields.Char(related='branch_id.phone', string="Phone",
                        help='Phone of specific branch', store=True)
    website = fields.Char(related='branch_id.website', string="Website",
                          help='Website of specific branch', store=True)
    allowed_branch_ids = fields.Many2many('res.branch',
                                          string="Allowed Branches",
                                          help='If set, Acts as default or '
                                               'allowed branches',
                                          compute='_compute_allowed_branch_ids')
    picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Operation Type',
        default=_default_picking_type_id,
        help='Specific stock picking type of the branch',
        required=True,
        domain="[('code', '=', 'outgoing'), "
               "('warehouse_id.company_id', '=', company_id),"
               "'|', ('warehouse_id.branch_id', '=', branch_id),"
               " ('warehouse_id.branch_id', '=', False)]",
        ondelete='restrict')
    journal_id = fields.Many2one(
        'account.journal', string='Sales Journal',
        domain=[('type', 'in', ('general', 'sale'))],
        help="Accounting journal used to post sales entries.",
        default=_default_sale_journal,
        ondelete='restrict')
    invoice_journal_id = fields.Many2one(
        'account.journal', string='Invoice Journal',
        domain=[('type', '=', 'sale')],
        help="Accounting journal used to create invoices.",
        default=_default_invoice_journal)

    @api.depends('company_id')
    def _compute_allowed_branch_ids(self):
        """method to compute allowed branches"""
        for pos in self:
            pos.allowed_branch_ids = self.env.user.branch_ids.ids

    @api.depends('company_id')
    def _compute_branch(self):
        """method to compute default branch"""
        for order in self:
            pos_company = order.company_id if order.company_id else \
                self.env.company
            branch_ids = self.env.user.branch_ids
            branch = branch_ids.filtered(
                lambda branch: branch.company_id == pos_company)
            if branch:
                order.branch_id = branch.ids[0]
            else:
                order.branch_id = False

    @api.onchange('branch_id')
    def onchange_branch(self):
        """on setting a branch arrange the journals of corresponding branch."""
        for pos in self:
            domain = [('branch_id', 'in', [pos.branch_id.id, False]),
                      ('company_id', '=', self.env.company.id)]
            picking = self.env['stock.warehouse'].search(domain, limit=1)
            sales_journal_domain = [
                                    ('branch_id', 'in',
                                     [pos.branch_id.id, False]),
                                    ('company_id', '=', self.env.company.id),
                                    ('type', 'in', ('sale', 'general')),
                                    ('code', 'ilike', 'POSS')]
            sales_journal = self.env['account.journal'].search(
                sales_journal_domain, limit=1)
            invoice_journal_domain = [('branch_id', 'in',
                                       [pos.branch_id.id, False]),
                                      ('company_id', '=', self.env.company.id),
                                      ('type', '=', 'sale')
                                      ]
            invoice_journal = self.env['account.journal'].search(
                invoice_journal_domain, limit=1)
            self.picking_type_id = picking.pos_type_id.id
            self.journal_id = sales_journal.id
            self.invoice_journal_id = invoice_journal.id
