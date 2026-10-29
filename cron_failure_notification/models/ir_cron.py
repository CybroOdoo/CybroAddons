# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(
#    <https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import datetime
import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    """Inherits ir.cron to record failure history and notify administrators
    when scheduled actions fail.
    """
    _inherit = 'ir.cron'

    def _callback(self, cron_name, server_action_id):
        """Run the method associated to a given job, and record failure
        history if an exception occurs.
        """
        self.ensure_one()
        try:
            return super()._callback(cron_name, server_action_id)
        except Exception as exception:
            try:
                self.env['failure.history'].sudo().create({
                    'name': cron_name,
                    'error': str(exception),
                })
            except Exception:
                _logger.exception(
                    "Failed to record failure history for cron %r",
                    cron_name,
                )
            raise

    def mail_send_cron(self):
        """If any cron failed in the past 24 hours, send a notification email
        to administrators with the failure report.
        """
        current_datetime = fields.Datetime.now()
        yesterday_datetime = current_datetime - datetime.timedelta(days=1)
        failures = self.env['failure.history'].search([
            ('create_date', '>=', yesterday_datetime),
            ('create_date', '<=', current_datetime),
        ])
        if not failures:
            return False

        admin_group = self.env.ref(
            'base.group_erp_manager', raise_if_not_found=False
        )
        if not admin_group:
            return False

        admin_emails = [
            user.email for user in admin_group.user_ids if user.email
        ]
        if not admin_emails:
            _logger.warning(
                "No administrator email found for cron failure notification."
            )
            return False

        email_values = {
            'email_to': ','.join(set(admin_emails)),
        }
        mail_template = self.env.ref(
            'cron_failure_notification.mail_template_cron_error',
            raise_if_not_found=False,
        )
        if not mail_template:
            _logger.warning(
                "Mail template mail_template_cron_error not found."
            )
            return False

        cron_rec = self.ensure_one() if len(self) == 1 else self[:1]
        if not cron_rec:
            cron_rec = self.env['ir.cron'].search([], limit=1)

        res_id = cron_rec.id if cron_rec else False
        mail_template.send_mail(
            res_id,
            email_values=email_values,
            force_send=True,
        )
        return True
