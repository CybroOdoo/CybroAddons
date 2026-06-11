# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import http
from odoo.http import request
class BackgroundAccountingReportController(http.Controller):

    @http.route("/report/background_generate_accounting", type="json", auth="user")
    def background_generate_accounting(self, options=None, request_id=False, tab_id=False):
        """
        Called from the JS fetch interceptor when the user clicks
        'Print PDF' on an enterprise accounting report.

        `options` is the full options dict that the JS would normally
        POST to /account_reports/export — it includes:
            - report_id
            - date.date_from / date.date_to
            - comparison, filters, column_groups, etc.
        """
        if not options or not options.get("report_id"):
            return {"status": "error", "message": "Missing report_id in options"}
        if "account.report" not in request.env:
            return {"status": "error", "message": "account_reports module is not installed."}

        request.env["account.report"].generate_in_background(
            options,
            request_id=request_id,
            tab_id=tab_id,
            context=dict(request.env.context),
        )
        return {"status": "started"}