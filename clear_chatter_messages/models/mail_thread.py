# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
################################################################################
# -*- coding: utf-8 -*-

from odoo import api, models


class MailThread(models.AbstractModel):
    """Extend mail.thread to clear chatter messages."""
    _inherit = "mail.thread"

    @api.model
    def action_clear_chatter_messages(self, model, res_id):
        """Delete all chatter messages belonging to a record."""

        if not self.env.user.has_group("clear_chatter_messages.group_chatter_message_manager"):
            return False

        if not isinstance(model, str) or not model:
            return False

        if isinstance(res_id, bool) or not isinstance(res_id, int) or res_id <= 0:
            return False

        if model not in self.env:
            return False

        record = self.env[model].browse(res_id).exists()

        if not record:
            return False

        record.check_access("write")

        messages = self.env["mail.message"].sudo().search([
            ("model", "=", model),
            ("res_id", "=", res_id),
        ])

        messages.unlink()

        return True

