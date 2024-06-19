# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class SubscriptionPackage(models.Model):
    """This class inherits from the 'subscription.package' model and extends
    its functionality. It provides methods for sending subscription order
    details to customers and managing subscription limits."""
    _inherit = "subscription.package"

    recurrence_period_id = fields.Many2one("recurrence.period",
                                           string="Recurrence Period",
                                           help="The period of the recurrence")

    def send_subscription_order_to_customer(self):
        """Generates a mail and send to customer about the subscription order
        details."""
        template_id = self.env.ref(
            'website_subscription_package.mail_template_subscription_order')
        for rec in self:
            email_vals = {'message_type': 'notification',
                          'is_notification': True,
                          "model": 'subscription.package',
                          "res_id": rec.id}
            template_id.send_mail(
                rec.id, force_send=True,
                email_layout_xmlid=
                "mail.mail_notification_layout_with_responsible_signature",
                email_values=email_vals)
