# -*- coding: utf-8 -*-
"""Import Lots Controllers."""
###############################################################################
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import io

import openpyxl

from odoo import http
from odoo.http import request
from odoo.http.stream import content_disposition

XLSX_MIMETYPE = ('application/vnd.openxmlformats-officedocument.'
                 'spreadsheetml.sheet')


class ImportLots(http.Controller):
    """ Class to handle excel download """
    @http.route('/download/excel', type='http', auth="user")
    def download_excel_file(self):
        """ Download sample Excel sheet """
        # Create a new workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        # Add headers
        ws.append(['Lots', 'Product', 'Quantity'])
        # Add sample data
        data = [
            ('0000021', '[FURN_8220] Four Person Desk', 2.00),
            ('0000022', '[FURN_8220] Four Person Desk', 3.00),
            ('0000023', '[FURN_8900] Drawer Black', 6.00),
        ]
        for row in data:
            ws.append(row)
        # Save the workbook to a BytesIO buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        return request.make_response(buffer.getvalue(), headers=[
            ('Content-Type', XLSX_MIMETYPE),
            ('Content-Disposition', content_disposition('my_excel_file.xlsx')),
        ])
