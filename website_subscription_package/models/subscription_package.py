# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
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

    def close_limit_cron(self):
        """It Checks renew date, close date. It will send mail when renew
        date and also generates invoices based on the plan.
        It wil close the subscription automatically if renewal limit is
        exceeded."""
        pending_subscriptions = self.env['subscription.package'].search(
            [('stage_category', '=', 'progress')])
        today_date = fields.Date.today()
        pending_subscription = False
        for pending_subscription in pending_subscriptions:
            get_dates = self.find_renew_date(
                pending_subscription.next_invoice_date,
                pending_subscription.date_started,
                pending_subscription.plan_id.days_to_end)
            renew_date = get_dates['renew_date']
            end_date = get_dates['end_date']
            pending_subscription.close_date = get_dates['close_date']
            if today_date == pending_subscription.next_invoice_date:
                if pending_subscription.plan_id.invoice_mode == 'draft_invoice':
                    this_products_line = []
                    for rec in pending_subscription.product_line_ids:
                        rec_list = [0, 0, {'product_id': rec.product_id.id,
                                           'quantity': rec.product_qty,
                                           'price_unit': rec.unit_price,
                                           'discount': rec.product_id.subscription_discount,
                                           'tax_ids': rec.tax_id
                                           }]
                        this_products_line.append(rec_list)
                    self.env['account.move'].create(
                        {'move_type': 'out_invoice',
                         'invoice_date_due': today_date,
                         'invoice_payment_term_id': False,
                         'invoice_date': today_date,
                         'state': 'draft',
                         'subscription_id': pending_subscription.id,
                         'partner_id': pending_subscription.partner_invoice_id.id,
                         'currency_id': pending_subscription.partner_invoice_id.currency_id.id,
                         'invoice_line_ids': this_products_line
                         })
                    pending_subscription.write({
                        'to_renew': False,
                        'start_date': pending_subscription.next_invoice_date})
                    new_date = self.find_renew_date(
                        pending_subscription.next_invoice_date,
                        pending_subscription.date_started,
                        pending_subscription.plan_id.days_to_end)
                    pending_subscription.write(
                        {'close_date': new_date['close_date']})
                    self.send_renew_alert_mail(today_date,
                                               new_date['renew_date'],
                                               pending_subscription.id)
            if (today_date == end_date) and (
                    pending_subscription.plan_id.limit_choice != 'manual'):
                display_msg = ("<h5><i>The renewal limit has been exceeded "
                               "today for this subscription based on the "
                               "current subscription plan.</i></h5>")
                pending_subscription.message_post(body=display_msg)
                pending_subscription.is_closed = True
                reason = (self.env['subscription.package.stop'].search([
                    ('name', '=', 'Renewal Limit Exceeded')]).id)
                pending_subscription.close_reason = reason
                pending_subscription.closed_by = self.user_id
                pending_subscription.close_date = fields.Date.today()
                stage = (self.env['subscription.package.stage'].search([
                    ('category', '=', 'closed')]).id)
                values = {'stage_id': stage, 'to_renew': False,
                          'next_invoice_date': False}
                pending_subscription.write(values)
            self.send_renew_alert_mail(today_date, renew_date,
                                       pending_subscription.id)
        return dict(pending=pending_subscription)
