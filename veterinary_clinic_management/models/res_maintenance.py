# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _, Command
from odoo.exceptions import ValidationError


class ResMaintenance(models.Model):
    """
        Model to store maintenance details in veterinary clinic management.

        This model tracks maintenance tasks, their types, responsible employees,
        suppliers, states, and associated costs.
    """
    _name = 'res.maintenance'
    _rec_name = 'maintenance_no'
    _inherit = 'mail.thread'
    _description = 'Res Maintenance'

    maintenance_no = fields.Char(
        string="Maintenance No",
        default=lambda self: _('New'),
        copy=False,
        readonly=True,
        tracking=True,
        help="Unique number for each maintenance record."
    )
    type = fields.Char(
        string="Type",
        help="Type of maintenance activity.", required=True
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="res.partner",
        help="Name of the employee responsible for the maintenance.", required=True
    )
    date = fields.Date(
        string="Date",
        default=fields.Date.today(),
        copy="False",
        help="Date of the maintenance activity."
    )
    supplier_id = fields.Many2one(
        string="Supplier",
        comodel_name="res.partner",
        copy="False",
        help="Name of the supplier for the maintenance activity.", required=True
    )
    state = fields.Selection(
        [('new', 'New'), ('in-progress', 'In-Progress'), ('complete', 'Complete')],
        default="new",
        tracking=True,
        help="Current state of the maintenance activity."
    )
    maintenance_line_ids = fields.One2many(
        'maintenance.service.line',
        'maintenance_id',
        string="Maintenance Service",
        help="Details of the maintenance services provided."
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id.id,
        help="Currency used for the maintenance costs."
    )
    maintenance_total = fields.Monetary(
        compute="_compute_maintenance_total",
        string='Total',
        help="Total cost of the maintenance activity."
    )
    maintenance_bill_invoice_id = fields.Many2one(
        comodel_name='account.move',
        help="Invoice related to the maintenance activity."
    )
    is_invoiced = fields.Boolean(
        string="Invoiced",
        help="Indicates if an invoice has been generated for this maintenance activity."
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_count",
        help="Count of invoices related to this maintenance activity."
    )
    payment_ribbon = fields.Char(
        compute='_compute_payment_ribbon',
        help="Ribbon to indicate payment status."
    )

    @api.depends('maintenance_line_ids.subtotal')
    def _compute_maintenance_total(self):
        """
        Compute the total cost of the maintenance activity by summing the costs of all maintenance lines.
        """
        for record in self:
            record.maintenance_total = sum(record.maintenance_line_ids.mapped('subtotal'))

    @api.depends('maintenance_bill_invoice_id')
    def _compute_invoice_count(self):
        """
        Compute the count of invoices related to this maintenance activity.
        """
        for record in self:
            record.invoice_count = len(record.maintenance_bill_invoice_id)

    @api.depends('maintenance_bill_invoice_id')
    def _compute_payment_ribbon(self):
        """
        Compute the payment status badge based on whether an invoice has been generated.
        """
        for record in self:
            record.payment_ribbon = record.maintenance_bill_invoice_id.payment_state

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create method to assign maintenance appointment No.
        """
        for vals in vals_list:
            if vals.get('maintenance_no', 'New') == 'New':
                vals['maintenance_no'] = self.env['ir.sequence'].next_by_code('maintenance.sequence') or 'New'
        return super().create(vals_list)

    def action_create_invoice(self):
        """Create an invoice."""
        for record in self:
            lines = [Command.create({
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
            }) for line in record.maintenance_line_ids]

            if not lines:
                raise ValidationError(_("Please add at least one service before creating an invoice."))

            invoice = self.env['account.move'].create([{
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.context_today(record),
                'partner_id': record.employee_id.id,
                'currency_id': record.currency_id.id or self.env.company.currency_id.id,
                'maintenance_bill_invoice_id': record.id,
                'invoice_line_ids': lines
            }])
            record.maintenance_bill_invoice_id = invoice.id
            record.is_invoiced = True
            return {
                'name': _('Customer Invoices'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'context': {'default_move_type': 'out_invoice'},
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': invoice.id
            }

    def action_view_invoice(self):
        """Action to view the created invoice."""
        self.ensure_one()
        return {
            'name': _('Customer Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.maintenance_bill_invoice_id.id
        }
