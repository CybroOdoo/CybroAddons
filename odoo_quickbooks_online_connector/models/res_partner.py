# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
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
from odoo import fields, models


class ResPartner(models.Model):
    """Inherited res.partner to add additional fields related to quickbook"""
    _inherit = 'res.partner'

    qbooks_customer = fields.Char(string='Customer ID',
                                  help='Quickbook customer id')
    qbooks_vendor = fields.Char(string='Vendor ID', help='Quickbook vendor id')
    qbooks_sync_token = fields.Char(string='Sync Token',
                                    help='Quickbook Synchronization token')
    qbooks_tax_exempt = fields.Boolean(string='Tax Exempt',
                                       default=False,
                                       help='Indicates if this customer is tax exempt in QuickBooks')
