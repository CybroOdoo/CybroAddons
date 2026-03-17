# -- coding: utf-8 --
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
from datetime import date, timedelta

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring weight constants (must sum to 100)
# ---------------------------------------------------------------------------
WEIGHT_PURCHASE_RECENCY = 35   # Days since last sale order
WEIGHT_REVENUE_TREND = 25       # Revenue trend direction
WEIGHT_SUPPORT_BURDEN = 20      # Ticket volume + resolution quality
WEIGHT_CRM_ENGAGEMENT = 20      # Days since last CRM/message contact

# Thresholds (days)
PURCHASE_RECENCY_THRESHOLDS = [
    (30,  0),    # 0–30 days  → 0 pts
    (60,  10),   # 31–60 days → 10 pts
    (90,  20),   # 61–90 days → 20 pts
    (180, 28),   # 91–180 days → 28 pts
]
PURCHASE_RECENCY_MAX = 35        # 180+ days → max pts

CONTACT_THRESHOLDS = [
    (30, 0),     # 0–30 days  → 0 pts
    (60, 8),     # 31–60 days → 8 pts
    (90, 14),    # 61–90 days → 14 pts
]
CONTACT_MAX = 20                 # 90+ days → max pts

TICKET_90D_HIGH = 5              # >5 tickets in 90 days is "high volume"
AVG_RESOLUTION_SLOW = 48         # >48 h resolution is "slow"


def _score_from_thresholds(value, thresholds, max_score):
    """Return a score based on ascending threshold buckets.

    *thresholds* is a list of ``(upper_bound, score)`` pairs in ascending
    order.  If *value* exceeds all upper bounds, *max_score* is returned.
    """
    for upper, score in thresholds:
        if value <= upper:
            return score
    return max_score


class ChurnScore(models.Model):
    """Churn risk score for a single customer (res.partner)."""

    _name = 'churn.score'
    _description = 'Customer Churn Risk Score'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'churn_score desc, score_date desc'
    _rec_name = 'partner_id'

    # ------------------------------------------------------------------
    # Core fields
    # ------------------------------------------------------------------
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade',
        index=True,
        tracking=True,
    )
    churn_score = fields.Float(
        string='Churn Score',
        digits=(6, 2),
        default=0.0,
        tracking=True,
        help='0 = no risk, 100 = highest churn risk.',
    )
    risk_level = fields.Selection(
        selection=[
            ('low',      'Low'),
            ('medium',   'Medium'),
            ('high',     'High'),
            ('critical', 'Critical'),
        ],
        string='Risk Level',
        default='low',
        tracking=True,
    )
    score_date = fields.Date(
        string='Last Scored',
        default=fields.Date.today,
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Signal fields (raw data captured at scoring time)
    # ------------------------------------------------------------------
    last_purchase_days = fields.Integer(
        string='Days Since Last Purchase',
        help='Number of days elapsed since the most recent confirmed sale order.',
    )
    ticket_count_90d = fields.Integer(
        string='Support Tickets (90 days)',
        help='Number of helpdesk tickets opened in the last 90 days.',
    )
    avg_resolution_time = fields.Float(
        string='Avg. Resolution Time (h)',
        digits=(10, 2),
        help='Average time in hours to close a helpdesk ticket.',
    )
    last_contact_days = fields.Integer(
        string='Days Since Last Contact',
        help='Days since the most recent CRM activity or inbound/outbound message.',
    )
    revenue_trend = fields.Selection(
        selection=[
            ('growing',   'Growing'),
            ('stable',    'Stable'),
            ('declining', 'Declining'),
        ],
        string='Revenue Trend',
        default='stable',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Output fields
    # ------------------------------------------------------------------
    suggested_actions = fields.Text(
        string='Retention Recommendations',
        help='Rule-based retention action suggestions generated at scoring time.',
    )
    alert_sent = fields.Boolean(
        string='Alert Sent',
        default=False,
        help='True when a churn alert has already been dispatched for the '
             'current risk level.  Reset automatically when risk drops.',
        tracking=True,
    )

    # ------------------------------------------------------------------
    # Computed / relational helpers
    # ------------------------------------------------------------------
    company_id = fields.Many2one(
        related='partner_id.company_id',
        store=True,
        index=True,
    )
    user_id = fields.Many2one(
        related='partner_id.user_id',
        string='Account Manager',
        store=True,
    )
    color = fields.Integer(
        string='Color Index',
        compute='_compute_color',
        store=True,
    )

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    _sql_constraints = [
        ('partner_unique', 'UNIQUE(partner_id)',
         'A churn score record already exists for this customer.'),
    ]

    # ------------------------------------------------------------------
    # Computed fields
    # ------------------------------------------------------------------
    @api.depends('risk_level')
    def _compute_color(self):
        color_map = {
            'low':      10,  # green
            'medium':   3,   # yellow
            'high':     2,   # orange
            'critical': 1,   # red
        }
        for rec in self:
            rec.color = color_map.get(rec.risk_level, 0)

    # ------------------------------------------------------------------
    # Private helpers — data collection
    # ------------------------------------------------------------------

    def _get_last_purchase_days(self, partner):
        """Return days since the last confirmed sale order (0 if none)."""
        SaleOrder = self.env['sale.order']
        last_order = SaleOrder.search(
            [
                ('partner_id', 'child_of', partner.id),
                ('state', 'in', ['sale', 'done']),
            ],
            order='date_order desc',
            limit=1,
        )
        if not last_order:
            return 365  # no orders ever → treat as very stale
        delta = date.today() - last_order.date_order.date()
        return max(delta.days, 0)

    def _get_revenue_trend(self, partner):
        """Compare revenue of the last 3 months vs the 3 months before that.

        Returns 'growing', 'stable', or 'declining'.
        """
        AccountMove = self.env['account.move']
        today = date.today()
        m3_start = today - timedelta(days=90)
        m6_start = today - timedelta(days=180)

        def _revenue(date_from, date_to):
            moves = AccountMove.search([
                ('partner_id', 'child_of', partner.id),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', date_from),
                ('invoice_date', '<',  date_to),
            ])
            total = 0.0
            for move in moves:
                if move.move_type == 'out_invoice':
                    total += move.amount_untaxed
                else:
                    total -= move.amount_untaxed
            return total

        recent   = _revenue(m3_start, today)
        previous = _revenue(m6_start, m3_start)

        if previous == 0:
            return 'stable' if recent == 0 else 'growing'
        change_pct = (recent - previous) / abs(previous) * 100
        if change_pct >= 5:
            return 'growing'
        if change_pct <= -5:
            return 'declining'
        return 'stable'

    def _get_ticket_data(self, partner):
        """Return (ticket_count_90d, avg_resolution_hours).

        Gracefully returns (0, 0.0) when the helpdesk module is not installed.
        """
        if 'helpdesk.ticket' not in self.env:
            return 0, 0.0

        HelpdeskTicket = self.env['helpdesk.ticket']
        cutoff = date.today() - timedelta(days=90)

        tickets = HelpdeskTicket.search([
            ('partner_id', 'child_of', partner.id),
            ('create_date', '>=', fields.Datetime.to_string(cutoff)),
        ])
        count = len(tickets)

        # Average resolution time for closed tickets (hours)
        closed = tickets.filtered(
            lambda t: t.close_date and t.create_date
        )
        if closed:
            total_hours = sum(
                (t.close_date - t.create_date).total_seconds() / 3600
                for t in closed
            )
            avg_hours = total_hours / len(closed)
        else:
            avg_hours = 0.0

        return count, round(avg_hours, 2)

    def _get_last_contact_days(self, partner):
        """Return days since the last inbound/outbound message or CRM activity."""
        today = date.today()

        # 1. Latest mail.message on the partner thread or related records
        Message = self.env['mail.message']
        last_msg = Message.search(
            [
                ('res_id', '=', partner.id),
                ('model', '=', 'res.partner'),
                ('message_type', 'in', ['comment', 'email']),
            ],
            order='date desc',
            limit=1,
        )
        last_msg_date = last_msg.date.date() if last_msg else None

        # 2. Latest CRM lead/opportunity activity date
        CrmLead = self.env['crm.lead']
        last_lead = CrmLead.search(
            [('partner_id', 'child_of', partner.id)],
            order='date_last_stage_update desc',
            limit=1,
        )
        last_crm_date = None
        if last_lead and last_lead.date_last_stage_update:
            last_crm_date = last_lead.date_last_stage_update.date()

        # Pick the most recent of the two
        candidates = [d for d in [last_msg_date, last_crm_date] if d]
        if not candidates:
            return 365  # no contact data → treat as very stale
        latest = max(candidates)
        return max((today - latest).days, 0)

    # ------------------------------------------------------------------
    # Scoring engine
    # ------------------------------------------------------------------

    def _compute_score(self):
        """Calculate the churn score using the weighted formula.

        Weights
        -------
        Purchase recency : 35 %
        Revenue trend    : 25 %
        Support burden   : 20 %
        CRM engagement   : 20 %
        """
        self.ensure_one()
        partner = self.partner_id

        # --- Collect signals ---
        purchase_days   = self._get_last_purchase_days(partner)
        revenue_trend   = self._get_revenue_trend(partner)
        ticket_count, avg_resolution = self._get_ticket_data(partner)
        contact_days    = self._get_last_contact_days(partner)

        # --- Component 1: Purchase recency (35 pts max) ---
        purchase_score = _score_from_thresholds(
            purchase_days, PURCHASE_RECENCY_THRESHOLDS, PURCHASE_RECENCY_MAX
        )

        # --- Component 2: Revenue trend (25 pts max) ---
        trend_score_map = {'growing': 0, 'stable': 10, 'declining': 25}
        trend_score = trend_score_map.get(revenue_trend, 10)

        # --- Component 3: Support burden (20 pts max) ---
        # Ticket volume sub-score (0–10 pts)
        if ticket_count == 0:
            volume_pts = 0
        elif ticket_count <= 2:
            volume_pts = 3
        elif ticket_count <= TICKET_90D_HIGH:
            volume_pts = 6
        else:
            volume_pts = 10
        # Resolution quality sub-score (0–10 pts)
        if avg_resolution == 0.0:
            resolution_pts = 0
        elif avg_resolution <= 24:
            resolution_pts = 2
        elif avg_resolution <= AVG_RESOLUTION_SLOW:
            resolution_pts = 5
        else:
            resolution_pts = 10
        support_score = volume_pts + resolution_pts   # 0–20

        # --- Component 4: CRM engagement (20 pts max) ---
        engagement_score = _score_from_thresholds(
            contact_days, CONTACT_THRESHOLDS, CONTACT_MAX
        )

        # --- Total score ---
        total = purchase_score + trend_score + support_score + engagement_score
        total = max(0.0, min(100.0, float(total)))

        # --- Risk level ---
        if total >= 76:
            risk = 'critical'
        elif total >= 51:
            risk = 'high'
        elif total >= 26:
            risk = 'medium'
        else:
            risk = 'low'

        return {
            'churn_score':          total,
            'risk_level':           risk,
            'last_purchase_days':   purchase_days,
            'revenue_trend':        revenue_trend,
            'ticket_count_90d':     ticket_count,
            'avg_resolution_time':  avg_resolution,
            'last_contact_days':    contact_days,
            'score_date':           date.today(),
            'suggested_actions':    self._build_suggestions(
                purchase_days, revenue_trend, ticket_count,
                avg_resolution, contact_days
            ),
        }

    # ------------------------------------------------------------------
    # Retention suggestion builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_suggestions(purchase_days, revenue_trend, ticket_count,
                           avg_resolution, contact_days):
        """Return a human-readable retention action string based on signals."""
        suggestions = []

        if purchase_days > 90:
            suggestions.append(
                "• Schedule a check-in call and share a loyalty discount or "
                "exclusive offer to re-activate purchasing activity."
            )
        if ticket_count > TICKET_90D_HIGH or avg_resolution > AVG_RESOLUTION_SLOW:
            suggestions.append(
                "• Escalate any open support tickets immediately and offer a "
                "dedicated service review call with a senior account manager."
            )
        if contact_days > 60:
            suggestions.append(
                "• Assign a personalised re-engagement email sequence and "
                "schedule at least one touchpoint this week."
            )
        if revenue_trend == 'declining':
            suggestions.append(
                "• Revenue has been declining — arrange an upsell consultation "
                "or account review meeting to understand the customer's evolving needs."
            )
        if purchase_days > 180:
            suggestions.append(
                "• Customer has not purchased in over 6 months.  Consider a "
                "win-back campaign with a time-limited incentive."
            )
        if not suggestions:
            suggestions.append(
                "• Customer is in good standing.  Maintain regular contact "
                "cadence and monitor quarterly."
            )

        return "\n".join(suggestions)

    # ------------------------------------------------------------------
    # Automated alert dispatcher
    # ------------------------------------------------------------------

    def _dispatch_alert(self):
        """Create a CRM activity, post a chatter note, and mark alert_sent."""
        self.ensure_one()
        partner = self.partner_id

        # 1. Grab the specific system administrator (usually Mitchell Admin)
        fallback_user = self.env.ref('base.user_admin', raise_if_not_found=False)

        # 2. Try Salesperson -> then Mitchell Admin -> then default to OdooBot
        manager = partner.user_id or fallback_user or self.env.user

        risk_lbl = dict(self._fields['risk_level'].selection).get(
            self.risk_level, self.risk_level
        )

        subject = _(
            "Churn Alert — %(risk)s Risk: %(partner)s (Score: %(score).1f)",
            risk=risk_lbl,
            partner=partner.name,
            score=self.churn_score,
        )

        body = _(
            "<p><strong>Churn Risk Alert</strong></p>"
            "<p>Customer <strong>%(partner)s</strong> has been classified as "
            "<strong>%(risk)s</strong> risk with a churn score of "
            "<strong>%(score).1f / 100</strong>.</p>"
            "<p><u>Retention recommendations:</u></p>"
            "<pre>%(actions)s</pre>",
            partner=partner.name,
            risk=risk_lbl,
            score=self.churn_score,
            actions=self.suggested_actions or _('No suggestions available.'),
        )

        # Schedule a CRM activity for the assigned user
        activity_type = self.env.ref(
            'mail.mail_activity_data_todo', raise_if_not_found=False
        )
        if activity_type:
            self.activity_schedule(
                activity_type_id=activity_type.id,
                summary=subject,
                note=body,
                user_id=manager.id,
                date_deadline=date.today() + timedelta(days=2),
            )

        self.alert_sent = True



    # ------------------------------------------------------------------
    # Public API — single record scoring
    # ------------------------------------------------------------------

    def action_compute_score(self):
        """Manually trigger score (re-)computation from the form view."""
        for rec in self:
            vals = rec._compute_score()
            prev_risk = rec.risk_level
            rec.write(vals)
            # Reset alert if risk dropped back to low/medium
            if prev_risk in ('high', 'critical') and vals['risk_level'] in (
                'low', 'medium'
            ):
                rec.alert_sent = False

    # ------------------------------------------------------------------
    # Scheduled action entry-point (called by ir.cron)
    # ------------------------------------------------------------------

    @api.model
    def cron_compute_all_scores(self):
        """Daily cron: score all active customers and dispatch alerts."""
        _logger.info("ChurnPredictor — starting daily scoring run")

        # Find all customers (non-archived partners flagged as customers)
        partners = self.env['res.partner'].search([
            ('active', '=', True),
            ('is_company', '=', True),
            ('customer_rank', '>', 0),
        ])

        scored = 0
        alerted = 0

        for partner in partners:
            # Get or create the churn score record
            score_rec = self.search([('partner_id', '=', partner.id)], limit=1)
            if not score_rec:
                score_rec = self.create({'partner_id': partner.id})

            vals = score_rec._compute_score()
            prev_risk = score_rec.risk_level
            score_rec.write(vals)
            scored += 1

            new_risk = vals['risk_level']

            # Reset alert flag if risk has improved
            if prev_risk in ('high', 'critical') and new_risk in ('low', 'medium'):
                score_rec.alert_sent = False

            # Dispatch alert for newly high/critical records
            if new_risk in ('high', 'critical') and not score_rec.alert_sent:
                try:
                    score_rec._dispatch_alert()
                    alerted += 1
                except Exception as exc:
                    _logger.warning(
                        "ChurnPredictor — failed to dispatch alert for partner "
                        "%s (id=%s): %s",
                        partner.name, partner.id, exc,
                    )

