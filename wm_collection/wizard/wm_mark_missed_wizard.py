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

from markupsafe import escape, Markup
from odoo import fields, models, _
from odoo.exceptions import UserError


class WmMarkMissedWizard(models.TransientModel):

    """Wizard to mark a collection order as missed, capture the reason, and optionally reschedule."""
    _name = 'wm.mark.missed.wizard'
    _description = 'Mark Collection as Missed'

    order_id = fields.Many2one(
        'wm.collection.order', string='Collection Order',
        required=True, readonly=True)
    reason_id = fields.Many2one(
        'wm.missed.reason', string='Reason',
        required=True, domain=[('active', '=', True)])
    notes = fields.Text(string='Driver Notes', help='Provides information about driver notes')

    def action_confirm(self):
        """
        Orchestrate the full missed-collection flow (E1 → E2 → E3).
        """
        self.ensure_one()
        use_missed = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_missed_collection', 'False') in ('True', '1')
        if not use_missed:
            raise UserError(_("Missed Collection functionality is disabled in settings."))

        order = self.order_id

        # Mark the order as missed
        order.with_context(
            programmatic_state_change=True,
            skip_schedule_date_check=True,
        ).write({
            'state': 'missed',
            'is_missed': True,
            'missed_reason_id': self.reason_id.id,
            'missed_notes': self.notes,
        })

        # Create the missed-collection record
        missed_vals = {
            'order_id': order.id,
            'reason_id': self.reason_id.id,
            'driver_id': order.driver_id.id,
            'notes': self.notes,
            'missed_date': fields.Datetime.now(),
        }

        # Auto-create retry order for the next day
        retry_start = fields.Datetime.now() + timedelta(days=1)
        if order.scheduled_start and order.scheduled_end and order.scheduled_end > order.scheduled_start:
            duration = order.scheduled_end - order.scheduled_start
        else:
            duration = timedelta(hours=2)
        retry_end = retry_start + duration

        retry_vals = {
            'state': 'draft',
            'name': 'New',
            'parent_order_id': order.id,
            'scheduled_start': retry_start,
            'scheduled_end': retry_end,
            'actual_start': False,
            'actual_end': False,
            'is_missed': False,
            'missed_reason_id': False,
            'missed_notes': False,
            'completed_date': False,
            'signature_id': False,
            'driver_photo': False,
            'geolocation_tag': False,
            'order_line_ids': [(0, 0, {
                'category_id': line.category_id.id if line.category_id else False,
                'product_id': line.product_id.id if line.product_id else False,
                'estimated_weight': line.estimated_weight,
                'weight': line.weight,
            }) for line in order.order_line_ids],
        }
        if 'consolidated_invoice_id' in order._fields:
            retry_vals['consolidated_invoice_id'] = False

        retry_order = order.copy(retry_vals)
        order.retry_order_id = retry_order.id

        missed_vals['retry_order_id'] = retry_order.id

        missed_record = self.env['wm.missed.collection'].create(missed_vals)
        order.missed_collection_id = missed_record.id

        # Auto-notify customer via email template
        template = self.env.ref(
            'wm_collection.mail_template_missed_collection',
            raise_if_not_found=False)
        if template and order.partner_id:
            template.send_mail(order.id, force_send=True)
            missed_record.customer_notified = True

        # Log in chatter
        order.message_post(
            body=Markup(_(
                "Collection marked as missed.<br/>"
                "<b>Reason:</b> %(reason)s<br/>"
                "<b>Retry Order:</b> %(retry)s"
            )) % {
                'reason': escape(self.reason_id.name or ''),
                'retry': escape(retry_order.name or ''),
            },
            message_type='notification',
        )

        return {'type': 'ir.actions.act_window_close'}
