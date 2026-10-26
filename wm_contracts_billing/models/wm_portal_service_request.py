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

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class WmPortalServiceRequest(models.Model):
    """Model tracking customer self-service requests submitted via the customer portal."""
    _name = 'wm.portal.service.request'
    _description = 'Waste Management Portal Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Request Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        default=lambda self: self.env.user.partner_id,
        tracking=True,
        index=True,
    )
    contract_id = fields.Many2one(
        'wm.partner.contract',
        string='Contract',
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
    )
    collection_point_id = fields.Many2one(
        'wm.collection.point',
        string='Collection Site / Location',
        required=True,
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
    )
    request_type = fields.Selection([
        ('extra_pickup', 'Extra / Bulky Pickup Request'),
        ('container_swap', 'Container Swap / Resize Request'),
        ('missed_collection', 'Report Missed Collection'),
        ('service_hold', 'Temporary Service Hold / Pause'),
    ], string='Request Type', required=True, default='extra_pickup', tracking=True)

    category_id = fields.Many2one(
        'wm.waste.category',
        string='Waste Category',
        help='Waste category for extra pickup request.'
    )
    requested_date = fields.Date(
        string='Requested Date',
        required=True,
        default=fields.Date.today,
        help='Preferred date for pickup, container swap, or service request.'
    )

    hold_start_date = fields.Date(
        string='Hold Start Date',
        help='Start date for temporary service hold.'
    )
    hold_end_date = fields.Date(
        string='Hold End Date',
        help='End date for temporary service hold.'
    )
    container_type_id = fields.Many2one(
        'wm.container.type',
        string='New Container Type',
        help='Desired container type for swap/resize request.'
    )
    notes = fields.Text(string='Customer Notes / Instructions')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    rejection_reason = fields.Text(string='Rejection Reason', readonly=True, copy=False, tracking=True)

    collection_order_id = fields.Many2one(
        'wm.collection.order',
        string='Generated Collection Order',
        readonly=True,
        ondelete='set null',
        copy=False,
    )
    missed_collection_id = fields.Many2one(
        'wm.missed.collection',
        string='Linked Missed Collection Report',
        readonly=True,
        ondelete='set null',
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    base_estimated_price = fields.Monetary(
        string='Base Estimated Price',
        currency_field='currency_id',
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assign sequence number on creation.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.portal.service.request') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        """
        Customer submits service request from portal or draft.
        """
        for req in self:
            if req.state != 'draft':
                continue
            req.write({'state': 'submitted'})
            req.message_post(body=_("Service request %s submitted by customer.") % req.name)
            # Create activity for operations / contract team
            group_ref = self.env.ref('wm_contracts_billing.group_wm_contract_manager', raise_if_not_found=False) or self.env.ref('wm_base.group_wm_ops_manager', raise_if_not_found=False)
            managers = (group_ref.all_user_ids or group_ref.user_ids) if group_ref else self.env['res.users']
            if managers:
                req.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_("New Customer Service Request: %s") % req.name,
                    note=_("Customer %s submitted request: %s") % (req.partner_id.name, req.get_request_type_display()),
                    user_id=managers[0].id
                )

    # Groups allowed to process (approve / reject / complete) service requests.
    # Keep in sync with the groups= on the header buttons of the form view.
    _PROCESSING_GROUPS = (
        'wm_base.group_wm_dispatcher',
        'wm_base.group_wm_ops_manager',
        'wm_contracts_billing.group_wm_contract_manager',
        'wm_base.group_wm_admin',
    )

    def _check_backoffice_user(self):
        """
        Approving, rejecting or completing a request creates collection orders
        and billable events, so it is reserved for dispatchers, operations
        managers, contract managers and WM administrators. Other users
        (drivers, recyclers, finance, plain internal users, portal customers)
        may view requests but not process them. Superuser (sudo) flows are
        always allowed.
        """
        if self.env.su:
            return
        user = self.env.user
        if not any(user.has_group(group) for group in self._PROCESSING_GROUPS):
            raise AccessError(_(
                "Only dispatchers, operations managers, contract managers or "
                "waste management administrators can process service requests."
            ))

    def action_approve(self):
        """
        Operations officer approves the service request and triggers backend records.
        """
        self._check_backoffice_user()
        for req in self:
            if req.state not in ('submitted', 'draft'):
                raise UserError(_("Only submitted or draft requests can be approved."))

            req.state = 'approved'
            req.message_post(body=_("Service request approved by %s.") % self.env.user.name)

            if req.request_type == 'extra_pickup' and not req.collection_order_id:
                # Generate draft collection order
                req_date = req.requested_date or fields.Date.today()
                start_dt = fields.Datetime.to_datetime(req_date)
                end_dt = start_dt + timedelta(hours=1)
                order_vals = {
                    'partner_id': req.partner_id.id,
                    'collection_point_id': req.collection_point_id.id if req.collection_point_id else False,
                    'contract_id': req.contract_id.id if req.contract_id else False,
                    'scheduled_start': start_dt,
                    'scheduled_end': end_dt,
                    'state': 'draft',
                    'portal_request_id': req.id,
                }
                new_order = self.env['wm.collection.order'].sudo().create(order_vals)
                if req.category_id:
                    self.env['wm.collection.order.line'].sudo().create({
                        'order_id': new_order.id,
                        'category_id': req.category_id.id,
                    })
                req.collection_order_id = new_order.id
                req.message_post(body=_("Generated Collection Order: %s") % new_order.name)

                if 'wm.billable.event' in self.env:
                    event = self.env['wm.billable.event'].sudo().create({
                        'partner_id': req.partner_id.id,
                        'collection_point_id': req.collection_point_id.id if req.collection_point_id else False,
                        'event_type': 'extra_pickup',
                        'collection_order_id': new_order.id,
                        'portal_request_id': req.id,
                        'event_date': req.requested_date or fields.Date.today(),
                        'quantity': 1.0,
                        # Subscriber benefit (wm_subscription): must reach the invoice,
                        # not only the estimate shown on the request.
                        'discount_pct': getattr(req, 'subscriber_discount_pct', 0.0) or 0.0,
                        'state': 'confirmed',
                    })
                    req.message_post(body=_("Generated Billable Event: %s (%s)") % (event.name, event.rate_source))

            elif req.request_type == 'missed_collection' and not req.missed_collection_id:
                # Generate missed collection report if wm_missed_collection exists
                if 'wm.missed.collection' in self.env:
                    missed_vals = {
                        'partner_id': req.partner_id.id,
                        'collection_point_id': req.collection_point_id.id if req.collection_point_id else False,
                        'missed_date': req.requested_date or fields.Date.today(),
                        'reason': 'customer_reported',
                        'notes': _("Reported by customer via portal request %s.\n%s") % (req.name, req.notes or ''),
                    }
                    missed_rec = self.env['wm.missed.collection'].sudo().create(missed_vals)
                    req.missed_collection_id = missed_rec.id
                    req.message_post(body=_("Logged Missed Collection Report %s.") % missed_rec.display_name)

            elif req.request_type == 'service_hold':
                if 'wm.subscription' in self.env:
                    domain = [('partner_id', '=', req.partner_id.id), ('state', '=', 'active')]
                    if req.contract_id:
                        domain.append(('contract_id', '=', req.contract_id.id))
                    active_sub = self.env['wm.subscription'].sudo().search(domain, limit=1)
                    if active_sub:
                        active_sub.action_pause(resume_date=req.hold_end_date)
                        msg = _("Service hold approved. Paused active subscription %s until %s.") % (
                            active_sub.name, req.hold_end_date or _('N/A')
                        )
                        req.message_post(body=msg)
                        if req.contract_id:
                            req.contract_id.message_post(body=msg)
                    else:
                        msg = _("Service hold approved. Note: No active subscription found for customer %s to pause.") % req.partner_id.name
                        req.message_post(body=msg)
                        if req.contract_id:
                            req.contract_id.message_post(body=msg)
                else:
                    msg = _("Service hold approved until %s.") % (req.hold_end_date or _('N/A'))
                    req.message_post(body=msg)
                    if req.contract_id:
                        req.contract_id.message_post(body=msg)

    def action_open_reject_wizard(self):
        """Ask for the rejection reason before rejecting the request."""
        self.ensure_one()
        self._check_backoffice_user()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Reject Service Request"),
            'res_model': 'wm.portal.request.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    def action_reject(self, reason=None):
        """
        Reject a submitted service request. Once a request has been approved
        its records exist and it can only be cancelled, not rejected.
        """
        self._check_backoffice_user()
        for req in self:
            if req.state != 'submitted':
                raise UserError(_("Only submitted requests can be rejected. Approved requests can be cancelled instead."))
        for req in self:
            req.write({'state': 'rejected', 'rejection_reason': reason or False})
            msg = _("Service request rejected.")
            if reason:
                msg += _(" Reason: %s") % reason
            req.message_post(body=msg)

    def action_complete(self):
        """
        Mark service request as completed.
        """
        self._check_backoffice_user()
        for req in self:
            if req.state not in ('approved', 'in_progress'):
                raise UserError(_("Only approved or in-progress requests can be completed."))
            req.state = 'completed'
            req.message_post(body=_("Service request marked as completed."))

    def action_cancel(self):
        """
        Cancel a draft, submitted or approved service request. Cancelling an
        approved request also cancels the collection order and billable event
        that were generated on approval, unless work has already started or the
        event has been invoiced.
        """
        self._check_backoffice_user()
        for req in self:
            if req.state not in ('draft', 'submitted', 'approved'):
                raise UserError(_("Only draft, submitted or approved requests can be cancelled."))
            if req.state == 'approved':
                req._check_generated_records_cancellable()
        for req in self:
            was_approved = req.state == 'approved'
            req.state = 'cancelled'
            req.message_post(body=_("Service request cancelled."))
            if was_approved:
                req._cancel_generated_records()

    def _check_generated_records_cancellable(self):
        """Raise if the records generated on approval can no longer be cancelled."""
        self.ensure_one()
        order = self.collection_order_id
        if order and order.state not in ('draft', 'dispatched', 'cancelled'):
            raise UserError(_(
                "Collection order %(order)s is already %(state)s, so request %(request)s can no longer be cancelled.",
                order=order.name, state=order.state, request=self.name))
        if 'wm.billable.event' in self.env:
            invoiced = self.env['wm.billable.event'].sudo().search_count([
                ('portal_request_id', '=', self.id), ('state', '=', 'invoiced')])
            if invoiced:
                raise UserError(_(
                    "A billable event of request %s has already been invoiced, so it can no longer be cancelled.",
                    self.name))

    def _cancel_generated_records(self):
        """Cancel the collection order and billable events generated on approval."""
        self.ensure_one()
        order = self.collection_order_id.sudo()
        if order and order.state != 'cancelled':
            order.action_cancel()
            self.message_post(body=_("Collection order %s cancelled.") % order.name)
        if 'wm.billable.event' in self.env:
            events = self.env['wm.billable.event'].sudo().search([
                ('portal_request_id', '=', self.id), ('state', '!=', 'cancelled')])
            if events:
                events.action_cancel()
                self.message_post(body=_("Billable event(s) %s cancelled.") % ", ".join(events.mapped('name')))
        if self.request_type == 'service_hold':
            self.message_post(body=_(
                "Note: the subscription paused for this service hold is not resumed automatically. "
                "Resume it manually if required."))

    def get_request_type_display(self):
        """
        Helper method to return request type display text.
        """
        return dict(self._fields['request_type'].selection).get(self.request_type, '')
