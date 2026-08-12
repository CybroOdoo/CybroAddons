# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

from datetime import timedelta
from collections import defaultdict
from odoo import models, fields, api


class ResPartner(models.Model):
    """
    This class is Inheriting the model res.partner.
     add some extra fields and functions for the model.
    """
    _inherit = "res.partner"

    helpdesk_ticket_ids = fields.One2many(
        'helpdesk.ticket',
        'partner_id',
        string="Helpdesk Tickets",
        help="Displays all support tickets linked to this customer, used to calculate health and sentiment metrics."

    )

    customer_health_score = fields.Integer(
        string="Customer Health Score",
        compute="_compute_customer_health",
        store=True,
        help="Overall stability rating from 0 to 100. This is a weighted average of AI-analyzed sentiment, ticket "
             "frequency in the last 30 days, and unresolved critical issues."
    )

    customer_health_label = fields.Char(
        string="Customer Health Status",
        compute="_compute_customer_health",
        store=True,
        help="Human-readable status of the account health (e.g., Healthy, Attention Needed, or Critical Risk) based "
             "on the current health score."
    )

    is_at_risk = fields.Boolean(
        string="At Risk",
        compute="_compute_customer_health",
        store=True,
        help="If checked, this account is in a 'Critical' state (score of 35 or lower) and requires immediate"
             " intervention."
    )

    @api.depends('helpdesk_ticket_ids.sentiment_score', 'helpdesk_ticket_ids.stage_id')
    def _compute_customer_health(self):
        """Calculates a weighted customer health score (0-100) based on recent ticket volume, critical issues, and average AI sentiment."""
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
            ('create_date', '>=', ninety_days_ago)
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
            total_sentiment = 0.0

            for t in tickets_90d:
                score = t.sentiment_score
                is_closed = getattr(t.stage_id, 'is_close', False) or getattr(t.stage_id, 'fold',
                                                                              False)

                if is_closed and score < 0:
                    score = score / 2.0

                total_sentiment += score

                if t.create_date >= thirty_days_ago:
                    volume_30d += 1
                if t.create_date >= sixty_days_ago and score <= -0.6:
                    critical_60d += 1

            avg_score = total_sentiment / len(tickets_90d)
            sentiment_pts = int((avg_score + 1) * 30)

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
