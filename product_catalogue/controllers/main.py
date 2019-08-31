# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sayooj A O(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import http
from odoo.http import request


class CataloguePrint(http.Controller):
    """This class includes the function which fetch the details
    about the corresponding product and print catalogue in
    PDF format"""

    @http.route(['/report/pdf/catalogue_download'], type='http', auth='public')
    def download_catalogue(self, product_id):
        """In this function we are calling the report template
        of the corresponding product and
        downloads the catalogue in pdf format"""
        pdf, _ = request.env.ref('product_catalogue.action_report_product_catalog')\
            .sudo().render_qweb_pdf([int(product_id)])
        pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf)),
                          ('Content-Disposition', 'catalogue' + '.pdf;')]
        return request.make_response(pdf, headers=pdfhttpheaders)
