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
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class WmContainer(models.Model):
    """
    Represents an individual physical container/bin unit identified by a barcode/tag,
    tracking deployment location, current status, physical condition, and lift history.
    """
    _name = 'wm.container'
    _description = 'Individual Container / Bin Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']
    _order = 'name asc, id desc'

    name = fields.Char(
        string='Barcode / Tag',
        required=True,
        index=True,
        copy=False,
        tracking=True,
        help='Unique barcode, RFID tag, or printed serial identifier for the physical unit.'
    )
    container_type_id = fields.Many2one(
        'wm.container.type',
        string='Container Spec / Type',
        required=True,
        index=True,
        ondelete='restrict',
        tracking=True,
        help='Specification, volume, and tare weight definition of this container.'
    )
    collection_point_id = fields.Many2one(
        'wm.collection.point',
        string='Deployed Site',
        index=True,
        ondelete='set null',
        tracking=True,
        help='Current collection point where this container unit is deployed (blank if in yard).'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='collection_point_id.partner_id',
        store=True,
        readonly=True,
    )
    status = fields.Selection([
        ('in_yard', 'In Yard'),
        ('deployed', 'Deployed'),
        ('needs_cleaning', 'Needs Cleaning'),
        ('damaged', 'Damaged'),
        ('awaiting_pickup', 'Awaiting Pickup'),
    ], string='Status', default='in_yard', required=True, tracking=True, index=True)

    condition_notes = fields.Text(
        string='Condition Notes',
        help='Maintenance, physical condition notes, or damage details.'
    )
    deployed_date = fields.Date(
        string='Deployed Date',
        tracking=True,
        help='Date when this unit landed at its current site — used for rental duration billing.'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    last_invoiced_date = fields.Date(
        string='Last Invoiced Date',
        copy=False,
        readonly=True,
        help='Date up to which rental has been invoiced; the next rental invoice bills from this date.'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    rental_rate = fields.Monetary(
        string='Rental Rate',
        default=50.0,
        currency_field='currency_id',
        tracking=True,
        help='Rental fee for this container unit based on the selected billing period.'
    )
    rental_period = fields.Selection([
        ('daily', 'Per Day'),
        ('weekly', 'Per Week'),
        ('monthly', 'Per Month'),
        ('flat', 'Flat Fee'),
    ], string='Billing Period', default='monthly', required=True, tracking=True, help='Billing cycle/frequency for container rental (Per Day, Per Week, Per Month, or Flat Fee).')
    invoice_ids = fields.Many2many(
        'account.move',
        'wm_container_invoice_rel',
        'container_id',
        'move_id',
        string='Rental Invoices',
        copy=False,
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count',
    )

    # Lift / Service history from waste.batch
    batch_ids = fields.One2many(
        'waste.batch',
        'container_id',
        string='Service / Lift History',
    )
    lift_count = fields.Integer(
        string='Total Lifts',
        compute='_compute_lift_count',
        store=True,
    )

    _barcode_uniq = models.Constraint(
        'unique(name, company_id)',
        'The container barcode / tag must be unique per company!'
    )

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        """Compute total rental invoices created for this container."""
        for container in self:
            container.invoice_count = len(container.invoice_ids)

    @api.depends('batch_ids')
    def _compute_lift_count(self):
        """Compute the total number of service/lift pickups logged for this container."""
        for container in self:
            container.lift_count = len(container.batch_ids)

    def action_view_invoices(self):
        """Smart button action to view rental invoices generated for this container."""
        self.ensure_one()
        invoices = self.invoice_ids
        if not invoices:
            return None
        action = {
            'name': _('Container Rental Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoices.ids)],
        }
        if len(invoices) == 1:
            action['view_mode'] = 'form'
            action['res_id'] = invoices.id
        return action

    def action_create_rental_invoice(self):
        """Create a rental invoice directly from the physical container unit form."""
        self.ensure_one()
        user = self.env.user
        if not (self.env.su or user.has_group('wm_base.group_wm_finance')
                or user.has_group('account.group_account_invoice')):
            raise AccessError(_("Only finance users can create container rental invoices."))
        if not self.partner_id:
            raise UserError(_("Cannot create a rental invoice: This container is not currently deployed to a customer collection point."))
        if self.rental_rate <= 0:
            raise UserError(_("Container %s has no rental rate (it is rented out free of charge): nothing to invoice.") % self.name)

        period_label = dict(self._fields['rental_period'].selection).get(self.rental_period, self.rental_period)
        today = fields.Date.today()
        # Bill from the last invoiced date of the current deployment; a
        # redeployment (deployed_date after it) starts a fresh billing run.
        already_billed = bool(self.last_invoiced_date) and (
            not self.deployed_date or self.last_invoiced_date >= self.deployed_date)
        billing_start = self.last_invoiced_date if already_billed else self.deployed_date
        if self.rental_period == 'flat':
            # A flat fee is charged once per deployment.
            if already_billed:
                raise UserError(_(
                    "The flat rental fee for container %(name)s has already been invoiced for this deployment.",
                    name=self.name,
                ))
            qty, billed_until = 1.0, today
        elif not billing_start:
            # No deployment date known: nothing to count from, bill one period.
            qty, billed_until = 1.0, today
        else:
            qty, billed_until = self._rental_full_periods(billing_start, today)
            if qty <= 0:
                raise UserError(_(
                    "No full %(period)s rental period has elapsed for container %(name)s since %(date)s.",
                    period=period_label.lower(), name=self.name, date=billing_start,
                ))

        invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'invoice_date': today,
            'invoice_line_ids': [(0, 0, {
                'name': _("Container Rental Fee — %(tag)s (%(type)s) [%(period)s, Site: %(site)s]") % {
                    'tag': self.name,
                    'type': self.container_type_id.name if self.container_type_id else _('Standard Unit'),
                    'period': period_label,
                    'site': self.collection_point_id.name if self.collection_point_id else _('Deployed Site'),
                },
                'quantity': qty,
                'price_unit': self.rental_rate,
            })],
        })
        self.sudo().write({
            'invoice_ids': [(4, invoice.id)],
            'last_invoiced_date': billed_until,
        })
        return {
            'name': _('Rental Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _rental_full_periods(self, start, end):
        """Return (number of full rental periods between start and end, end
        date of the last full period). Partial periods are not counted so they
        carry over to the next invoice."""
        self.ensure_one()
        if not start or not end or end <= start:
            return 0, start
        if self.rental_period == 'daily':
            periods = (end - start).days
            return periods, start + relativedelta(days=periods)
        if self.rental_period == 'weekly':
            periods = (end - start).days // 7
            return periods, start + relativedelta(weeks=periods)
        if self.rental_period == 'monthly':
            delta = relativedelta(end, start)
            periods = delta.years * 12 + delta.months
            return periods, start + relativedelta(months=periods)
        return 0, start

    @api.onchange('collection_point_id')
    def _onchange_collection_point_id(self):
        """Auto-set status to 'deployed' and deployed_date to today when assigned to a collection point, or reset to 'in_yard' when removed."""
        if self.collection_point_id:
            if self.status in ('in_yard', 'awaiting_pickup'):
                self.status = 'deployed'
            if not self.deployed_date:
                self.deployed_date = fields.Date.today()
        else:
            if self.status == 'deployed':
                self.status = 'in_yard'
            self.deployed_date = False

    def action_view_batches(self):
        """Smart button action to view lift history (waste batches)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Service / Lift History'),
            'res_model': 'waste.batch',
            'view_mode': 'list,form',
            'domain': [('container_id', '=', self.id)],
            'context': {'default_container_id': self.id, 'default_container_type_id': self.container_type_id.id},
        }


class WmContainerTypeInherit(models.Model):
    _inherit = 'wm.container.type'

    individual_container_ids = fields.One2many(
        'wm.container',
        'container_type_id',
        string='Individual Container Units',
    )
    unit_count = fields.Integer(
        string='Total Units',
        compute='_compute_unit_count',
    )

    @api.depends('individual_container_ids')
    def _compute_unit_count(self):
        """Compute count of individual physical units for this container type spec."""
        for ctype in self:
            ctype.unit_count = len(ctype.individual_container_ids)

    def action_view_individual_containers(self):
        """Smart button action to view physical container units of this spec."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Physical Container Units'),
            'res_model': 'wm.container',
            'view_mode': 'list,form',
            'domain': [('container_type_id', '=', self.id)],
            'context': {'default_container_type_id': self.id},
        }
