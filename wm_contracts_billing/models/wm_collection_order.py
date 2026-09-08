# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WmCollectionOrder(models.Model):
    """Extends Collection Order with contract determination and consolidated billing fields."""
    _inherit = 'wm.collection.order'

    # Contract Fields
    contract_id = fields.Many2one(
        'wm.partner.contract', string='Contract',
        compute='_compute_contract_id', store=True, precompute=True, ondelete='set null'
    )
    contract_product_ids = fields.Many2many(
        'product.product',
        compute='_compute_contract_product_ids',
        string='Contract Waste Materials',
        help='Waste materials allowed by the contract. If empty, any waste material can be selected.'
    )

    # Billing Fields
    consolidated_invoice_id = fields.Many2one(
        'wm.consolidated.invoice',
        string='Consolidated Invoice',
        readonly=True,
        ondelete='set null',
        copy=False,
        help="The consolidated invoice that covers this collection order's charges.",
    )
    billing_run_line_id = fields.Many2one(
        'wm.monthly.billing.run.line',
        string='Monthly Billing Run Line',
        readonly=True,
        ondelete='set null',
        copy=False,
        help="The monthly billing run line that includes this collection order.",
    )
    is_consolidated = fields.Boolean(
        string='Consolidated',
        compute='_compute_is_consolidated',
        store=True,
        help="True when this order has been included in a consolidated invoice.",
    )

    @api.depends('partner_id', 'collection_point_id')
    def _compute_contract_id(self):
        """
        Compute the active ongoing contract for the customer/collection point.
        """
        for order in self:
            if order.state != 'draft':
                order.contract_id = order._origin.contract_id
                continue

            if order.contract_id:
                contract = order.contract_id
                if order.partner_id and contract.partner_id == order.partner_id and contract.state == 'ongoing':
                    continue

            if order.partner_id:
                domain = [
                    ('partner_id', '=', order.partner_id.id),
                    ('state', '=', 'ongoing'),
                ]
                if order.collection_point_id:
                    domain.append(('collection_point_ids', 'in', order.collection_point_id.id))

                ongoing_contract = self.env['wm.partner.contract'].search(domain, limit=1)

                if not ongoing_contract and order.collection_point_id:
                    ongoing_contract = self.env['wm.partner.contract'].search([
                        ('partner_id', '=', order.partner_id.id),
                        ('state', '=', 'ongoing'),
                    ], limit=1)

                order.contract_id = ongoing_contract.id if ongoing_contract else False
            else:
                order.contract_id = False

    @api.depends(
        'contract_id',
        'contract_id.contract_line_ids',
        'contract_id.contract_line_ids.product_ids',
        'contract_id.contract_line_ids.category_id'
    )
    def _compute_contract_product_ids(self):
        """
        Compute waste material products specified in the active contract.
        """
        for order in self:
            if order.contract_id and order.contract_id.contract_line_ids:
                allowed_products = self.env['product.product']
                for line in order.contract_id.contract_line_ids:
                    if line.product_ids:
                        allowed_products |= line.product_ids
                    elif line.category_id:
                        cat_products = self.env['product.product'].search([
                            ('is_waste_material', '=', True),
                            ('wm_waste_category_id', '=', line.category_id.id),
                        ])
                        allowed_products |= cat_products
                order.contract_product_ids = allowed_products
            else:
                order.contract_product_ids = False

    @api.depends('contract_id', 'contract_id.contract_line_ids.category_id', 'collection_point_id', 'collection_point_id.category_ids')
    def _compute_collection_point_category_ids(self):
        """
        Derive the list of waste categories serviced at the collection point,
        used to filter and default the contract line category selection in the
        billing form.
        """
        super()._compute_collection_point_category_ids()
        for order in self:
            if order.contract_id and order.contract_id.contract_line_ids:
                order.collection_point_category_ids = order.contract_id.contract_line_ids.category_id

    @api.depends('consolidated_invoice_id', 'billing_run_line_id')
    def _compute_is_consolidated(self):
        """
        Determine whether this collection order has been included in a
        consolidated invoice run, preventing duplicate billing and showing a
        consolidated invoice badge.
        """
        for order in self:
            order.is_consolidated = bool(order.consolidated_invoice_id or order.billing_run_line_id)

    @api.depends('consolidated_invoice_id', 'billing_run_line_id')
    def _compute_is_billed(self):
        """
        Flag the collection order as billed once a linked invoice or billing
        run line reaches a confirmed/posted state, locking further billing
        actions on this order.
        """
        for order in self:
            order.is_billed = bool(order.consolidated_invoice_id or order.billing_run_line_id)

    @api.constrains('consolidated_invoice_id', 'billing_run_line_id')
    def _check_single_billing_pipeline(self):
        """
        Database constraint: order cannot be claimed by both billing pipelines.
        """
        for order in self:
            if order.consolidated_invoice_id and order.billing_run_line_id:
                raise ValidationError(_(
                    "Collection Order %s cannot be claimed by both a Consolidated Invoice "
                    "and a Monthly Billing Run Line."
                ) % order.name)

    _check_single_billing_pipeline_constraint = models.Constraint(
        'CHECK(NOT (consolidated_invoice_id IS NOT NULL AND billing_run_line_id IS NOT NULL))',
        'A collection order cannot be billed by both consolidated invoice and monthly billing run.'
    )
