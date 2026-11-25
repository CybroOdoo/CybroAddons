# -*- coding: utf-8 -*-
#############################################################################
#
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
#############################################################################
import logging
from odoo import api, fields, models
import dateutil.parser

_logger = logging.getLogger(__name__)


class OraCallHistory(models.Model):
    """Stores call logs, transcripts, and metadata for voice assistant sessions."""
    _name = "ora.call.history"
    _description = "Voice Assistant Call History"
    _order = "create_date desc"
    _rec_name = "name"

    name = fields.Char(
        string="Reference",
        default=lambda self: self.env['ir.sequence'].next_by_code('ora.call.history') or 'Call',
        readonly=True,
        help="Sequential reference number for this call log."
    )
    vapi_call_id = fields.Char(
        string="Vapi Call ID",
        index=True,
        copy=False,
        readonly=True,
        help="Unique identifier of the call assigned by Vapi."
    )
    assistant_id = fields.Many2one(
        "ora.ai",
        ondelete="set null",
        readonly=True,
        help="The AI voice assistant configuration used for this call session."
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        ondelete="set null",
        readonly=True,
        help="The customer or contact associated with this call."
    )
    user_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        ondelete="set null",
        readonly=True,
        help="The salesperson who initiated or was assigned to this voice call."
    )
    order_id = fields.Many2one(
        "sale.order",
        string="Generated Sale Order",
        ondelete="set null",
        readonly=True,
        help="The sales order created during this voice assistant session."
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Generated Invoice",
        ondelete="set null",
        readonly=True,
        help="The customer invoice created during this voice assistant session."
    )
    created_partner_id = fields.Many2one(
        "res.partner",
        string="Created Customer",
        ondelete="set null",
        readonly=True,
        help="The customer or contact created during this voice assistant session."
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Created Product",
        ondelete="set null",
        readonly=True,
        help="The product template created during this voice assistant session."
    )
    call_type = fields.Selection([
        ('inboundPhoneCall', 'Inbound Phone'),
        ('webCall', 'Web Call'),
        ('outboundPhoneCall', 'Outbound Phone'),
    ], default='webCall', readonly=True,
       help="Type of the call (e.g., Web Call, Inbound Phone, Outbound Phone).")
    start_time = fields.Datetime(
        readonly=True,
        help="Timestamp when the voice call started."
    )
    end_time = fields.Datetime(
        readonly=True,
        help="Timestamp when the voice call ended."
    )
    duration = fields.Integer(
        string="Duration (seconds)",
        default=0,
        readonly=True,
        help="Total duration of the voice call in seconds."
    )
    status = fields.Selection([
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], string="Call Status", default='started', readonly=True,
       help="Current execution status of the call (Started, Completed, or Failed).")
    transcript = fields.Text(
        string="Full Transcript",
        readonly=True,
        help="Full dialogue transcript recorded between the user and AI assistant."
    )
    recording_url = fields.Char(
        string="Recording URL",
        readonly=True,
        help="External URL where the recorded audio of this call can be accessed."
    )
    cost = fields.Float(
        string="Call Cost",
        digits=(16, 4),
        default=0.0,
        readonly=True,
        help="Calculated external provider cost for processing this call."
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        readonly=True,
        help="Company context under which this call took place."
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True,
        help="Currency used for reporting the call cost."
    )

    _uniq_vapi_call_id = models.Constraint('UNIQUE(vapi_call_id)', 'A call record with this Vapi Call ID already exists!')

    def action_view_sale_order(self):
        """Navigates to the linked Sale Order."""
        self.ensure_one()
        if not self.order_id:
            return False
        return {
            'name': 'Sale Order',
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoice(self):
        """Navigates to the linked Customer Invoice."""
        self.ensure_one()
        if not self.invoice_id:
            return False
        return {
            'name': 'Customer Invoice',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_created_partner(self):
        """Navigates to the linked Created Customer."""
        self.ensure_one()
        if not self.created_partner_id:
            return False
        return {
            'name': 'Customer',
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.created_partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_product(self):
        """Navigates to the linked Created Product."""
        self.ensure_one()
        if not self.product_tmpl_id:
            return False
        return {
            'name': 'Product',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': self.product_tmpl_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def log_call_status(self, data):
        """Processes incoming Vapi status updates or end-of-call reports idempotently."""
        if not data:
            return False

        message = data.get('message', {}) if isinstance(data, dict) else {}
        msg_type = message.get('type') or data.get('type')
        if msg_type not in ('status-update', 'end-of-call-report'):
            # Ignore high-frequency speech/interim events to avoid lock contention
            return False

        call = message.get('call', {}) or {}
        call_id = call.get('id') or data.get('call_id') or message.get('call_id')
        if not call_id:
            return False

        record = self.sudo().search([('vapi_call_id', '=', call_id)], limit=1)
        if msg_type == 'status-update' and message.get('status') == 'in-progress' and record:
            return record

        call_type = call.get('type') or 'webCall'
        assistant_vapi_id = call.get('assistantId')
        assistant = False
        if assistant_vapi_id:
            assistant = self.env['ora.ai'].sudo().search([('id_assistant', '=', assistant_vapi_id)], limit=1)

        # Extract transcript if available
        raw_transcript = message.get('transcript') or call.get('transcript')
        if not raw_transcript:
            conv = message.get('conversation') or call.get('conversation') or []
            if isinstance(conv, list):
                raw_transcript = "\n".join([f"{m.get('role', 'speaker')}: {m.get('content', '')}" for m in conv if isinstance(m, dict) and m.get('role') != 'system'])

        # Calculate duration or costs
        duration = 0
        raw_duration = (
            message.get('durationSeconds') or
            call.get('durationSeconds') or
            data.get('durationSeconds') or
            message.get('duration') or
            call.get('duration') or
            data.get('duration')
        )
        if raw_duration:
            try:
                duration = int(round(float(raw_duration)))
            except (ValueError, TypeError):
                duration = 0

        if not duration and (message.get('durationMs') or call.get('durationMs') or data.get('durationMs')):
            try:
                ms = message.get('durationMs') or call.get('durationMs') or data.get('durationMs')
                duration = int(round(float(ms) / 1000.0))
            except (ValueError, TypeError):
                duration = 0

        started_at = message.get('startedAt') or call.get('startedAt') or data.get('startedAt')
        ended_at = message.get('endedAt') or call.get('endedAt') or data.get('endedAt')
        if not duration and started_at and ended_at:
            try:
                s_dt = dateutil.parser.isoparse(started_at)
                e_dt = dateutil.parser.isoparse(ended_at)
                duration = int(round((e_dt - s_dt).total_seconds()))
            except Exception:
                duration = 0

        costs = message.get('cost') or call.get('cost') or data.get('cost') or 0.0
        recording_url = message.get('recordingUrl') or call.get('recordingUrl') or data.get('recordingUrl') or False

        vals = {
            'call_type': call_type,
            'duration': duration or (record.duration if record else 0),
            'cost': float(costs) if costs else (record.cost if record else 0.0),
        }
        if assistant:
            vals['assistant_id'] = assistant.id

        # Resolve salesperson
        assistant_overrides = call.get('assistantOverrides') or {}
        var_values = assistant_overrides.get('variableValues') or call.get('variableValues') or {}
        metadata = call.get('metadata') or data.get('metadata') or {}
        salesperson_id = (
            var_values.get('salesperson_id') or
            var_values.get('user_id') or
            metadata.get('salesperson_id') or
            metadata.get('user_id')
        )
        if salesperson_id:
            try:
                u = self.env['res.users'].sudo().browse(int(salesperson_id))
                if u.exists():
                    vals['user_id'] = u.id
            except (ValueError, TypeError) as err:
                _logger.debug("Failed to resolve salesperson from call metadata: %s", err)
        if raw_transcript:
            vals['transcript'] = raw_transcript
        if recording_url:
            vals['recording_url'] = recording_url
        if msg_type == 'end-of-call-report' or message.get('endedReason'):
            vals['status'] = 'completed'

        # Auto-link sale order if not yet linked
        if not (record and record.order_id) and call_id:
            linked_so = self.env['sale.order'].sudo().search([
                '|',
                ('origin', '=', f"Voice Assistant ({call_id[:8]})"),
                ('origin', 'ilike', call_id[:8])
            ], limit=1)
            if linked_so:
                vals['order_id'] = linked_so.id
                if not vals.get('partner_id') and linked_so.partner_id:
                    vals['partner_id'] = linked_so.partner_id.id
                if not vals.get('user_id') and linked_so.user_id:
                    vals['user_id'] = linked_so.user_id.id

        # Auto-link invoice if not yet linked
        if not (record and record.invoice_id) and call_id:
            linked_inv = self.env['account.move'].sudo().search([
                ('move_type', '=', 'out_invoice'),
                '|',
                ('invoice_origin', '=', f"Voice Assistant ({call_id[:8]})"),
                ('invoice_origin', 'ilike', call_id[:8])
            ], limit=1)
            if linked_inv:
                vals['invoice_id'] = linked_inv.id
                if not vals.get('partner_id') and linked_inv.partner_id:
                    vals['partner_id'] = linked_inv.partner_id.id

        if record:
            record.write(vals)
        else:
            vals.update({
                'vapi_call_id': call_id,
                'name': f"Call-{call_id[:8]}" if call_id else "Call",
                'status': 'completed' if msg_type == 'end-of-call-report' else 'started',
            })
            record = self.sudo().create(vals)

        return record


