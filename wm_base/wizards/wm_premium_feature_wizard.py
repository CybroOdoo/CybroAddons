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
from odoo import api, fields, models


class WmPremiumFeatureWizard(models.TransientModel):
    """Information dialog opened by the placeholder menus of paid add-ons.

    The placeholder menus live in this free module so that the paid modules are
    visible before they are installed; each paid module hides its own placeholders
    when it is installed.
    """
    _name = 'wm.premium.feature.wizard'
    _description = 'Premium Add-on Information'

    feature = fields.Selection(
        [('subscription', 'Subscriptions'), ('subscription_plan', 'Subscription Plans'),
         ('driver_app', 'Driver Mobile App')],
        required=True, default='subscription')
    title = fields.Char(compute='_compute_content')
    summary = fields.Char(compute='_compute_content')
    details = fields.Html(compute='_compute_content', sanitize=False)
    module_name = fields.Char(compute='_compute_content')

    def _get_feature_content(self):
        """Return the text shown for each premium feature."""
        return {
            'subscription': {
                'title': self.env._("Customer Subscriptions"),
                'summary': self.env._("Recurring subscriptions with weight quotas, automatic cycle invoices and renewals."),
                'paragraphs': [
                    self.env._("A subscription ties a customer contract to a plan. It tracks the weight allowance used "
                      "in each cycle, the container swaps and extra pickups included, and the SLA level promised."),
                    self.env._("Every cycle the recurring fee is invoiced automatically. Collections that fall inside the "
                      "allowance are covered by the subscription and only the excess is billed, so the monthly "
                      "billing run never charges the same pickup twice."),
                ],
            },
            'driver_app': {
                'title': self.env._("Driver Mobile App"),
                'summary': self.env._("An offline-first mobile app for drivers to log every collection stop."),
                'paragraphs': [
                    self.env._("Drivers install the app on their phone and update each stop with one tap: En Route, "
                      "Arrived, Started, Lifted, Weighed and Completed or Flagged. GPS coordinates are captured "
                      "with every update."),
                    self.env._("Updates are queued on the phone when there is no signal and sent automatically when the "
                      "connection returns, without ever being logged twice."),
                ],
            },
            'subscription_plan': {
                'title': self.env._("Subscription Plans"),
                'summary': self.env._("A reusable catalogue of Monthly, Quarterly and Annual plans with their benefits."),
                'paragraphs': [
                    self.env._("A plan defines the recurring fee, the billing cycle, the weight quota, the container swap "
                      "quota, the discount on extra pickups and the SLA level."),
                    self.env._("Plans are defined once and reused for every customer subscription, so a change of price or "
                      "allowance is made in one place."),
                ],
            },
        }

    @api.depends('feature')
    def _compute_content(self):
        content = self._get_feature_content()
        for wizard in self:
            data = content.get(wizard.feature, {})
            wizard.title = data.get('title', '')
            wizard.summary = data.get('summary', '')
            wizard.details = ''.join('<p>%s</p>' % p for p in data.get('paragraphs', []))
            wizard.module_name = {'driver_app': 'wm_driver_app'}.get(wizard.feature, 'wm_subscription')

    def action_get_addon(self):
        """Open the vendor website where the paid add-on can be obtained."""
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://www.cybrosys.com',
            'target': 'new',
        }
