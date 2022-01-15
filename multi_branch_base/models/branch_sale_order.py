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


class SaleOrder(models.Model):
    """inherited sale order"""
    _inherit = 'sale.order'

    @api.model
    def _default_warehouse_id(self):
        """methode to get default warehouse id"""
        # !!! Any change to the default value may have to be repercuted
        # on _init_column() below.
        return self.env.user._get_default_warehouse_id()

    branch_id = fields.Many2one("res.branch", string='Branch', store=True,
                                readonly=False,
                                compute="_compute_branch")
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)],
                                              'sent': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True,
        )

    @api.depends('company_id')
    def _compute_branch(self):
        for order in self:
            company = self.env.company
            so_company = order.company_id if order.company_id else self.env.company
            branch_ids = self.env.user.branch_ids
            branch = branch_ids.filtered(
                lambda branch: branch.company_id == so_company)
            if branch:
                order.branch_id = branch.ids[0]
            else:
                order.branch_id = False


    @api.constrains('branch_id', 'partner_id')
    def _check_partner_branch_id(self):
        """methode to check branch of partner and sale order"""
        for order in self:
            branch = order.partner_id.branch_id
            if branch and branch != order.branch_id:
                raise ValidationError(_(
                    "Your quotation customer have company branch "
                    "%(partner_branch)s whereas your quotation belongs to "
                    "company branch %(quote_branch)s. \n Please change the "
                    "company of your quotation or change the customer from "
                    "other branch",
                    partner_branch=branch.name,
                    quote_branch=order.branch_id.name,
                ))

    @api.constrains('branch_id', 'order_line')
    def _check_order_line_branch_id(self):
        """methode to check branch of products and sale order"""
        for order in self:
            branches = order.order_line.product_id.branch_id
            if branches and branches != order.branch_id:
                bad_products = order.order_line.product_id.filtered(
                    lambda p: p.branch_id and p.branch_id != order.branch_id)
                raise ValidationError(_(
                    "Your quotation contains products from company branch "
                    "%(product_branch)s whereas your quotation belongs to "
                    "company branch %(quote_branch)s. \n Please change the "
                    "company of your quotation or remove the products from "
                    "other companies (%(bad_products)s).",
                    product_branch=', '.join(branches.mapped('name')),
                    quote_branch=order.branch_id.name,
                    bad_products=', '.join(bad_products.mapped('display_name')),
                ))



    def _prepare_invoice(self):
        """override prepare_invoice function to include branch"""
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        branch_id = self.branch_id.id
        domain = [('branch_id', '=', branch_id),
                  ('type', '=', 'sale'),
                  ('code', '!=', 'POSS'),('company_id', '=', self.company_id.id)]

        journal = None
        if self._context.get('default_currency_id'):
            currency_domain = domain + [
                ('currency_id', '=', self._context['default_currency_id'])]
            journal = self.env['account.journal'].search(currency_domain,
                                                         limit=1)

        if not journal:
            journal = self.env['account.journal'].search(domain, limit=1)
        if not journal:
            domain = [('type', '=', 'sale'), ('code', '!=', 'POSS'),
                      ('branch_id', '=', False), ('company_id', '=', self.company_id.id)]
            journal = self.env['account.journal'].search(domain, limit=1)
        if not journal:
            error_msg = _(
                "No journal could be found in the '%s' branch"
                " for any of those types: sale",
                self.branch_id.name,
            )
            raise UserError(error_msg)

        invoice_vals['branch_id'] = self.branch_id.id or False
        invoice_vals['journal_id'] = journal.id
        return invoice_vals

    @api.onchange('branch_id')
    def onchange_branch_id(self):
        """onchange methode"""

        if self.branch_id and self.branch_id not in self.env.user.branch_ids and self.env.user.branch_ids:
            raise UserError("Unauthorised Branch")
        self.warehouse_id = False
        if self.branch_id:
            warehouse = self.env['stock.warehouse'].sudo().search(
                [('branch_id', '=', self.branch_id.id), ('company_id', '=', self.company_id.id)], limit=1)
            self.warehouse_id = warehouse
            if not warehouse:

                warehouse = self.env['stock.warehouse'].sudo().search([
                    ('branch_id', '=', False), ('company_id', '=', self.company_id.id)], limit=1)
                self.warehouse_id = warehouse
            if not warehouse:
                error_msg = _(
                    "No warehouse could be found in the '%s' branch",
                    self.branch_id.name
                )
                raise UserError(error_msg)
        else:

            self.warehouse_id = self.env['stock.warehouse'].sudo().search([
                ('branch_id', '=', False), ('company_id', '=', self.company_id.id)],
                limit=1)


class SaleOrderLine(models.Model):
    """inherited purchase order line"""
    _inherit = 'sale.order.line'

    branch_id = fields.Many2one(related='order_id.branch_id',
                                string='Branch', store=True)
