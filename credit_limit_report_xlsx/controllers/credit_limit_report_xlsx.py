# -*- coding: utf-8 -*-
###############################################################################

#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ATHUL RAJ B S(Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#    USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape


class CreditLimitReport(http.Controller):
    """Class for xlsx report
       get_report_xlsx(output_format):
                This function is for creation of xlsx report of credit limit
                 of customer"""

    @http.route('/credit_xlsx_reports', type='http', auth='user',
                methods=['POST'], csrf=False)
    def get_report_xlsx(self, output_format, **kwargs):
        """This function sets a cookies and is returned, and if an error is
        occurred its also returned"""
        uid = request.session.uid
        wizard_id = kwargs.get('wizard_id')
        report_obj = request.env['credit.limit.report'].with_user(uid)
        token = 'dummy-because-api-expects-one'
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[('Content-Type', 'application/vnd.ms-excel'),
                             ('Content-Disposition',
                              content_disposition('Credit Limit Report.xlsx'))
                             ])
                report_obj.get_xlsx_report(response, wizard_id=wizard_id)
                response.set_cookie('fileToken', token)
            else:
                raise ValueError(
                    "Unsupported output format: {}".format(output_format))
            return response
        except Exception as e:
            se = http.serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
