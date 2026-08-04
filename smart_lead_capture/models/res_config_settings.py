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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class SmartLeadCaptureSettings(models.TransientModel):
    """
    Stores all Smart Lead Capture configuration:
    - Default salesperson for auto-assignment
    - Twilio credentials for WhatsApp notifications
    - Outbound webhook target URL
    """
    _inherit = 'res.config.settings'

    slc_default_salesperson_id = fields.Many2one(
        'res.users',
        string='Default Salesperson',
        help='All new leads from Google Form will be assigned to this person',
        config_parameter='smart_lead_capture.default_salesperson_id',
    )

    # ── WhatsApp / Twilio ────────────────────────────────────────────
    slc_twilio_account_sid = fields.Char(
        string='Twilio Account SID',
        config_parameter='smart_lead_capture.twilio_account_sid',
    )
    slc_twilio_auth_token = fields.Char(
        string='Twilio Auth Token',
        config_parameter='smart_lead_capture.twilio_auth_token',
    )
    slc_twilio_whatsapp_from = fields.Char(
        string='Twilio WhatsApp From',
        help='Format: whatsapp:+14155238886',
        config_parameter='smart_lead_capture.twilio_whatsapp_from',
    )
    slc_whatsapp_notify_number = fields.Char(
        string='Notify WhatsApp Number',
        help='Number to receive lead notifications. Format: whatsapp:+919876543210',
        config_parameter='smart_lead_capture.whatsapp_notify_number',
    )

    # ── Outbound webhook ─────────────────────────────────────────────
    slc_outbound_webhook_url = fields.Char(
        string='Outbound Webhook URL',
        help='URL to POST lead data when a lead is created or updated in Odoo',
        config_parameter='smart_lead_capture.outbound_webhook_url',
    )

