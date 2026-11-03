# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################

from collections import defaultdict
from datetime import timedelta
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    helpdesk_ticket_ids = fields.One2many(
        'helpdesk.ticket',
        'partner_id',
        string="Helpdesk Tickets",
        help="Displays all support tickets linked to this customer, used to "
             "calculate health and sentiment metrics."
    )

    customer_health_score = fields.Integer(
        compute="_compute_customer_health",
        store=True,
        help="Overall stability rating from 0 to 100. This is a weighted "
             "average of AI-analyzed sentiment, ticket frequency in the last "
             "30 days, and unresolved critical issues."
    )

    customer_health_label = fields.Char(
        string="Customer Health Status",
        compute="_compute_customer_health",
        store=True,
        help="Human-readable status of the account health (e.g., Healthy, "
             "Attention Needed, or Critical Risk) based on the current "
             "health score."
    )

    is_at_risk = fields.Boolean(
        string="At Risk",
        compute="_compute_customer_health",
        store=True,
        help="If checked, this account is in a 'Critical' state (score of 35 "
             "or lower) and requires immediate intervention."
    )

    @api.depends(
        'helpdesk_ticket_ids.sentiment_score',
        'helpdesk_ticket_ids.stage_id',
        'helpdesk_ticket_ids.create_date'
    )
    def _compute_customer_health(self):
        """Calculates a weighted customer health score (0-100) based on
        recent ticket volume, critical issues, and time-decayed AI sentiment.
        """
        now = fields.Datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        sixty_days_ago = now - timedelta(days=60)
        ninety_days_ago = now - timedelta(days=90)

        for partner in self:
            partner.customer_health_score = 100
            partner.customer_health_label = "Healthy 🟢"
            partner.is_at_risk = False

        all_tickets = self.env['helpdesk.ticket'].sudo().search([
            ('partner_id', 'in', self.ids),
            ('sentiment_score', '!=', False),
            ('create_date', '>=', ninety_days_ago),
        ])

        tickets_by_partner = defaultdict(list)
        for ticket in all_tickets:
            tickets_by_partner[ticket.partner_id.id].append(ticket)

        for partner in self:
            tickets_90d = tickets_by_partner.get(partner.id, [])
            if not tickets_90d:
                continue

            volume_30d = 0
            critical_60d = 0
            weighted_sentiment_sum = 0.0
            total_weight = 0.0

            for t in tickets_90d:
                score = t.sentiment_score
                is_closed = (
                    getattr(t.stage_id, 'is_close', False)
                    or getattr(t.stage_id, 'fold', False)
                )

                if is_closed and score < 0:
                    score = score / 2.0

                # 90-day intelligent sentiment decay: recent interactions carry
                # significantly more weight, enabling score recovery as
                # interactions improve.
                days_ago = max(0, (now - t.create_date).days)
                weight = max(
                    0.1,
                    (90.0 - min(90.0, float(days_ago))) / 90.0
                )
                weighted_sentiment_sum += score * weight
                total_weight += weight

                if t.create_date >= thirty_days_ago:
                    volume_30d += 1
                if t.create_date >= sixty_days_ago and score <= -0.6:
                    critical_60d += 1

            avg_score = (
                weighted_sentiment_sum / total_weight
                if total_weight > 0 else 0.0
            )
            sentiment_pts = int(round((avg_score + 1.0) * 30))

            volume_pts = 20
            if volume_30d >= 5:
                volume_pts = 0
            elif volume_30d >= 3:
                volume_pts = 5
            elif volume_30d >= 1:
                volume_pts = 15

            critical_pts = 20
            if critical_60d >= 2:
                critical_pts = 0
            elif critical_60d == 1:
                critical_pts = 10

            final_score = sentiment_pts + volume_pts + critical_pts
            final_score = max(0, min(100, final_score))

            partner.customer_health_score = final_score

            if final_score <= 35:
                partner.customer_health_label = "Critical Risk 🔴"
                partner.is_at_risk = True
            elif final_score <= 55:
                partner.customer_health_label = "Attention Needed 🟠"
                partner.is_at_risk = False
            elif final_score <= 75:
                partner.customer_health_label = "Stable 🟡"
                partner.is_at_risk = False
            else:
                partner.customer_health_label = "Healthy 🟢"
                partner.is_at_risk = False

    @api.model
    def _cron_recompute_customer_health(self):
        """Cron job to recompute customer health scores daily for all partners
        with helpdesk tickets, ensuring 90-day time decay is updated.
        """
        partners = self.search([('helpdesk_ticket_ids', '!=', False)])
        if partners:
            partners._compute_customer_health()
