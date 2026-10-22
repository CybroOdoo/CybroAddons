# -*- coding: utf-8 -*-
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
#############################################################################
from odoo import models, fields


class AnomalyReportPDF(models.AbstractModel):
    """
    PDF report class for account.anomaly.alert.

    When the report is triggered without pre-selected record IDs
    (e.g. from the action menu with no rows selected), Odoo passes
    an empty list. We fall back to all alerts ordered by risk.
    """
    _name = "report.account_anomaly_detector.report_anomaly_alerts_document"
    _description = "Anomaly Detection PDF Report"

    def _get_report_values(self, docids, data=None):
        company_ids = self.env.companies.ids
        if docids:
            docs = self.env["account.anomaly.alert"].browse(docids).filtered(
                lambda a: a.company_id.id in company_ids
            )
        else:
            docs = self.env["account.anomaly.alert"].search(
                [("company_id", "in", company_ids)],
                order="risk_level asc, anomaly_score desc",
            )

        critical_count = len(
            docs.filtered(lambda a: a.risk_level == "critical")
        )
        high_count = len(docs.filtered(lambda a: a.risk_level == "high"))
        medium_count = len(docs.filtered(lambda a: a.risk_level == "medium"))
        low_count = len(docs.filtered(lambda a: a.risk_level == "low"))

        return {
            "doc_ids": docs.ids,
            "doc_model": "account.anomaly.alert",
            "docs": docs,
            "data": data or {},
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "print_date": fields.Datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
