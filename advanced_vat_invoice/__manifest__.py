# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>))
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################

{
    'name': 'Saudi VAT Invoice /Saudi Electronic Invoice',
    'version': '16.0.1.0.0',
    'summary': 'Saudi VAT Invoice /Saudi E-Invoice /Saudi Electronic Invoice',
    'description': 'Saudi VAT Invoice /Saudi E-Invoice /Saudi Electronic Invoice',
    'author': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['base', 'account'],
    'images': ['static/description/banner.png'],
    'data': [
        'views/qr_config.xml',
        'views/qrcode_in_invoices.xml',
        'report/invoice_pdf.xml',
        'report/vat_invoice_report_template.xml',
        'views/vat_invoice_in_action.xml',
        'report/simplified_tax_report_template.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'AGPL-3',
}
