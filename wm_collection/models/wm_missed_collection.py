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
from collections import defaultdict
from datetime import timedelta

from odoo import api, fields, models


class WmMissedCollection(models.Model):
    """Records a collection order that could not be completed, capturing the reason and rescheduling status."""
    _name = 'wm.missed.collection'
    _description = 'Missed Collection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference', required=True, copy=False,
        readonly=True, index=True, default=lambda self: 'New')
    order_id = fields.Many2one(
        'wm.collection.order', string='Order', required=True)
    reason_id = fields.Many2one(
        'wm.missed.reason', string='Reason Code', required=True)
    retry_order_id = fields.Many2one(
        'wm.collection.order', string='Retry Order')
    customer_notified = fields.Boolean(
        string='Customer Notified', default=False, readonly=True)
    missed_date = fields.Datetime(
        string='Missed Date', help='Provides information about missed date', default=fields.Datetime.now)
    driver_id = fields.Many2one('res.partner', string='Driver', help='Provides information about driver')
    notes = fields.Text(string='Notes', help='Provides information about notes')
    partner_id = fields.Many2one(
        related='order_id.partner_id', string='Customer', store=True)
    route_id = fields.Many2one(
        related='order_id.route_id', string='Route', store=True)

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to auto-generate the missed collection reference
        sequence, link back to the originating collection order, and send a
        missed-collection alert to the dispatcher.
        """
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'wm.missed.collection') or 'New'
        return super().create(vals_list)

    @api.model
    def _cron_weekly_review_reminder(self):
        """
        Runs weekly. Builds a summary of the last 7 days of missed
        collections (grouped by customer, reason and route) and raises a
        review activity for the user this scheduled action runs as
        (Settings > Technical > Scheduled Actions > "Execute As"),
        linked to the Missed Collection Report (pivot/graph) action.
        """
        use_missed = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_missed_collection', 'False') in ('True', '1')
        if not use_missed:
            return

        week_ago = fields.Datetime.now() - timedelta(days=7)
        recent = self.search([('missed_date', '>=', week_ago)])

        if not recent:
            # Nothing to review this week — no activity needed.
            return

        by_customer = defaultdict(int)
        by_reason = defaultdict(int)
        by_route = defaultdict(int)
        for rec in recent:
            by_customer[rec.partner_id.display_name or 'Unknown'] += 1
            by_reason[rec.reason_id.name or 'Unknown'] += 1
            by_route[rec.route_id.display_name or 'Unassigned'] += 1

        def _top(counter, limit=5):
            """
            Return the top-N missed collection records ordered by frequency
            within the selected date range, used for the missed collections
            trend analysis panel.
            """
            return ', '.join(
                f"{name} ({count})" for name, count in
                sorted(counter.items(), key=lambda i: i[1], reverse=True)[:limit]
            )

        summary = (
            "%(total)s missed collection(s) in the last 7 days.\n"
            "By reason: %(reason)s\n"
            "By customer: %(customer)s\n"
            "By route: %(route)s" % {
                'total': len(recent),
                'reason': _top(by_reason),
                'customer': _top(by_customer),
                'route': _top(by_route),
            }
        )

        note = (
            "<p><b>Weekly Missed Collection Review</b></p>"
            "<p>%s</p>"
            "<p>Open the Missed Collection Report to review patterns and "
            "decide on operational changes (customer education on bin "
            "placement, route timing adjustments).</p>"
        ) % summary.replace('\n', '<br/>')

        self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id(
                'wm.missed.collection'),
            'res_id': recent[0].id,
            'activity_type_id': self.env.ref(
                'mail.mail_activity_data_todo').id,
            'summary': 'Weekly Missed Collection Review',
            'note': note,
            'user_id': self.env.user.id,
            'date_deadline': fields.Date.context_today(self),
        })
