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
from datetime import timedelta

from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class WmConsolidatedBillingWizard(models.TransientModel):
    """Wizard to create a consolidated invoice by selecting a customer, date range, and unbilled orders."""
    _name = 'wm.consolidated.billing.wizard'
    _description = 'Consolidated Billing Wizard'

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
    )
    date_from = fields.Date(
        string='From Date',
        required=True,
        default=lambda self: (fields.Date.today().replace(day=1) - relativedelta(months=1)),
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1) - timedelta(days=1),
    )
    order_ids = fields.Many2many(
        'wm.collection.order',
        'wm_billing_wizard_order_rel',
        'wizard_id',
        'order_id',
        string='Collection Orders',
    )
    order_count = fields.Integer(
        string='Orders Found',
        compute='_compute_order_count',
    )
    estimated_total_amount = fields.Float(
        string='Estimated Invoice Total',
        compute='_compute_estimated_total_amount',
        digits=(16, 2),
    )

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        """
        Validate that To Date is not earlier than From Date.
        """
        for record in self:
            if record.date_from and record.date_to and record.date_to < record.date_from:
                raise ValidationError(_("To Date cannot be earlier than From Date."))

    @api.depends('order_ids')
    def _compute_order_count(self):
        """
        Count the collection orders that match the current wizard filter
        criteria, showing how many orders will be bundled into the consolidated
        invoice.
        """
        for wizard in self:
            wizard.order_count = len(wizard.order_ids)

    @api.depends('order_ids', 'order_ids.order_line_ids.total_amount')
    def _compute_estimated_total_amount(self):
        """
        Pre-calculate the estimated invoice total from all selected collection
        orders, providing a summary figure before the consolidated invoice is
        confirmed and posted.
        """
        for wizard in self:
            wizard.estimated_total_amount = sum(
                wizard.order_ids.mapped('order_line_ids.total_amount')
            )

    @api.onchange('partner_id', 'date_from', 'date_to')
    def _onchange_filters(self):
        """
        Refresh the wizard's collection order selection when filter criteria
        (date range, partner, billing basis) change, ensuring the displayed
        orders reflect current filter state.
        """
        self.order_ids = self._fetch_eligible_orders()

    def _fetch_eligible_orders(self):
        """
        Return completed or signed, un-consolidated collection orders for the
        customer in the date range.
        """
        if not self.partner_id:
            return self.env['wm.collection.order']
        domain = [
            ('partner_id', '=', self.partner_id.id),
            ('state', 'in', ('completed', 'signed')),
            ('consolidated_invoice_id', '=', False),
            ('billing_run_line_id', '=', False),
            ('company_id', '=', self.company_id.id),
        ]
        if self.date_from:
            domain += [
                '|',
                ('actual_end', '>=', self.date_from),
                '&', ('actual_end', '=', False), ('scheduled_start', '>=', self.date_from),
            ]
        if self.date_to:
            domain += [
                '|',
                ('actual_end', '<=', self.date_to),
                '&', ('actual_end', '=', False), ('scheduled_start', '<=', self.date_to),
            ]
        return self.env['wm.collection.order'].search(domain)

    def action_fetch_orders(self):
        """
        Reload order_ids based on the current filter selection.
        """
        self.ensure_one()
        orders = self._fetch_eligible_orders()
        self.order_ids = orders
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'wm.consolidated.billing.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_consolidated_invoice(self):
        """
        Create the wm.consolidated.invoice record and generate the invoice.
        """
        self.ensure_one()
        if not self.order_ids:
            raise UserError(_("No collection orders selected. Please fetch orders and select at least one."))

        # Create the consolidated invoice record
        consolidated = self.env['wm.consolidated.invoice'].create({
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'order_ids': [(6, 0, self.order_ids.ids)],
        })

        # Generate the invoice immediately
        result = consolidated.action_generate_invoice()
        return result
