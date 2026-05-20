# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class OilContract(models.Model):
    _name = 'oil.contract'
    _description = 'Oil Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(
        string='Contract Reference', required=True, copy=False,
        readonly=True, default=lambda self: 'New')
    vendor_id = fields.Many2one(
        'res.partner', string='Vendor/Contractor', required=True,
        tracking=True)
    lease_id = fields.Many2one(
        'oil.lease.agreement', string='Lease Agreement',
        domain="[('state', '=', 'active')]", tracking=True,
        help="Lease agreement this contract operates under.")
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    amount = fields.Monetary(
        string='Contract Amount', currency_field='currency_id',
        tracking=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('billed', 'Billed'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    select_type = fields.Selection([
        ('project', 'Project'),
        ('reservoir', 'Reservoir'),
        ('equipment', 'Equipment'),
    ], string='Select Type', default='project', tracking=True)
    project_id = fields.Many2one('project.project', string='Project')
    reservoir_id = fields.Many2one('oil.reservoir', string='Reservoir')
    equipment_id = fields.Many2one(
        'maintenance.equipment', string='Equipment')
    expiry_warning = fields.Text(
        string='Expiry Warning', compute='_compute_expiry_warning',
        help="Warning if related lease or JV agreement has expired.")

    bill_id = fields.Many2one(
        'account.move', string='Associated Bill', readonly=True,
        copy=False)
    bill_count = fields.Integer(
        string='Bill Count', compute='_compute_bill_count')

    def _compute_bill_count(self):
        """Compute the number of vendor bills linked to this contract."""
        for record in self:
            record.bill_count = 1 if record.bill_id else 0

    def _compute_expiry_warning(self):
        """Shows warnings if related lease or JV agreement is expired."""
        for record in self:
            warnings = []
            if (record.lease_id
                    and record.lease_id.state == 'expired'):
                warnings.append(
                    _("Lease Agreement '%s' has expired.",
                      record.lease_id.name))
            record.expiry_warning = (
                '\n'.join(warnings) if warnings else False)

    @api.constrains('amount', 'select_type', 'project_id',
                     'reservoir_id', 'equipment_id')
    def check_fields(self):
        """Validate contract amount, date range, and required linked entity based on the selected type."""
        for record in self:
            if record.amount <= 0:
                raise UserError(_("Enter a Valid Amount"))
            if record.end_date < record.start_date:
                raise ValidationError(
                    _("End Date must be after Start Date"))
            if record.select_type == 'project' and not record.project_id:
                raise UserError(_("Please Select Project"))
            if (record.select_type == 'reservoir'
                    and not record.reservoir_id):
                raise UserError(_("Please Select Reservoir"))
            if (record.select_type == 'equipment'
                    and not record.equipment_id):
                raise UserError(_("Please Select Equipment"))

    @api.model_create_multi
    def create(self, vals_list):
        """Generate a unique sequence reference for new contract records."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.contract') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        """Confirm the contract after verifying the linked lease agreement is active."""
        self.ensure_one()
        if self.lease_id and self.lease_id.state != 'active':
            raise UserError(
                _("Cannot confirm: Lease Agreement '%s' is not active.",
                  self.lease_id.name))
        self.state = 'confirmed'
        return True

    def action_cancel(self):
        """Cancel the contract."""
        self.ensure_one()
        self.state = 'cancelled'
        return True

    def action_set_to_draft(self):
        """Resets an expired or cancelled contract back to draft."""
        self.ensure_one()
        if self.state not in ('expired', 'cancelled'):
            raise UserError(
                _("Only expired or cancelled contracts can be reset "
                  "to draft."))
        self.state = 'draft'
        return True

    def action_create_bill(self):
        """Create a vendor bill for the contract amount with analytic distribution from the linked project."""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(
                _("Only confirmed contracts can have bills created."))
        if self.bill_id:
            raise UserError(
                _("A bill has already been created for this contract."))

        analytic_distribution = {}
        if self.project_id and self.project_id.account_id:
            analytic_distribution = {
                self.project_id.account_id.id: 100
            }
        elif (self.reservoir_id
              and self.reservoir_id.project_id.account_id):
            analytic_distribution = {
                self.reservoir_id.project_id.account_id.id: 100
            }

        bill_vals = {
            'move_type': 'in_invoice',
            'partner_id': self.vendor_id.id,
            'invoice_date': fields.Date.today(),
            'currency_id': self.currency_id.id,
            'contract_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'name': _("Contract Payment for %s", self.name),
                'quantity': 1,
                'analytic_distribution': analytic_distribution,
                'price_unit': self.amount,
            })],
        }

        bill = self.env['account.move'].create(bill_vals)
        self.write({'bill_id': bill.id})
        return self.action_view_bill()

    def action_view_bill(self):
        """Open the form view of the associated vendor bill."""
        self.ensure_one()
        if not self.bill_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
            'target': 'current',
        }

    @api.model
    def cron_check_contract_expiry(self):
        """Scheduled action: expire confirmed contracts past end_date."""
        today = fields.Date.today()
        expired = self.search([
            ('state', 'in', ('draft', 'confirmed')),
            ('end_date', '<', today),
        ])
        for contract in expired:
            contract.write({'state': 'expired'})
            contract.message_post(
                body=_("Contract automatically expired on %s.", today),
                message_type='notification')
