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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request

class BackgroundReportController(http.Controller):

    @http.route('/report/background_generate', type='json', auth='user')
    def background_generate(self, report_name, docids, request_id=False, tab_id=False):
        """
            Start report PDF generation in the background.
            This controller route is called from the frontend to
            trigger background report generation without blocking
            the user interface.
        """
        request.env['ir.actions.report'].generate_in_background(
            report_name,
            docids,
            request_id=request_id,
            tab_id=tab_id,
            context=dict(request.env.context),
        )
        return {"status": "started"}