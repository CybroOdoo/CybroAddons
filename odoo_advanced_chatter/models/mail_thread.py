# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Prasudhi A(<https://www.cybrosys.com>)
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
from odoo import api, models, _


_logger = logging.getLogger(__name__)


class Message(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        """Override to filter recipients based on selected follower checkboxes"""
        recipients_data = super()._notify_get_recipients(message, msg_vals, **kwargs)

        # Check if we have selected follower partner IDs from checkboxes
        selected_follower_partner_ids = self._context.get('selected_follower_partner_ids')

        if selected_follower_partner_ids is not None:
            # Filter recipients to only include selected followers
            filtered_recipients = []
            _logger.info(f"DEBUG: _notify_get_recipients context selected_ids: {selected_follower_partner_ids}")

            # Ensure robust type comparison
            try:
                allowed_ids = set([int(pid) for pid in selected_follower_partner_ids])
            except (ValueError, TypeError):
                allowed_ids = set()
                _logger.warning(f"Invalid IDs in context: {selected_follower_partner_ids}")

            _logger.info(f"DEBUG: Initial recipients_data ids: {[r.get('id') for r in recipients_data]}")

            for recipient in recipients_data:
                partner_id = recipient.get('id')
                # Ensure we compare same types (integers)
                if partner_id in allowed_ids:
                    filtered_recipients.append(recipient)
                    _logger.info("Including recipient: %s", partner_id)
                else:
                    _logger.info(f"DEBUG: Excluding recipient (not checked): {partner_id}")

            _logger.info(f"Filtered {len(recipients_data)} recipients down to {len(filtered_recipients)}")
            return filtered_recipients

        return recipients_data

    def message_post(self, **kwargs):
        """Override to handle selected followers via context"""
        selected_follower_partner_ids = kwargs.pop('selected_follower_partner_ids', None)

        if selected_follower_partner_ids:
            _logger.info(f"DEBUG: message_post received selected_follower_partner_ids: {selected_follower_partner_ids}")

            # Ensure IDs are integers
            try:
                selected_ids = [int(pid) for pid in selected_follower_partner_ids]
            except (ValueError, TypeError):
                _logger.warning(f"Invalid partner IDs in selection: {selected_follower_partner_ids}")
                selected_ids = []

            if selected_ids:
                # CRITICAL: Override partner_ids to force all recipients (customer + followers) into ONE email
                # This combines everyone into a single recipient list
                kwargs['partner_ids'] = selected_ids

                # Disable separate follower notifications to prevent duplicate emails
                # Set mail_post_autofollow=False to prevent auto-adding followers separately
                self = self.with_context(
                    selected_follower_partner_ids=selected_ids,
                    mail_post_autofollow=False  # Prevent automatic follower notifications
                )
        return super(Message, self).message_post(**kwargs)


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model_create_multi
    def create(self, vals_list):
        # Check if we are in our custom flow
        selected_ids = self._context.get('selected_follower_partner_ids')
        if selected_ids:
            _logger.info("DEBUG: MailMail create intercepting for selected_ids injection")
            # We want to ensure these IDs are present in the recipient_ids of the generated mail
            # This is a brute-force approach but very reliable
            
            for vals in vals_list:
                # recipient_ids is a command list e.g. [(6, 0, [id, id])] or [(4, id), (4, id)]
                # Safest way: if recipient_ids exists, modify it. If not, create it.
                
                existing_commands = vals.get('recipient_ids', [])
                if existing_commands:
                   # Try to add selected_ids via (4, id) command to append
                   commands_to_add = [(4, pid) for pid in selected_ids]
                   
                   # Avoid duplicates if we can parse existing commands, but (4, id) is idempotent usually?
                   # Actually (4, id) is safe even if already linked.
                   vals['recipient_ids'] = existing_commands + commands_to_add
                else:
                   # Create new list
                   # Check if no recipient_ids provided? Usually we must have.
                   vals['recipient_ids'] = [(4, pid) for pid in selected_ids]
            
        return super().create(vals_list)
