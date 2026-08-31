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


class AccountTax(models.Model):
    """Inherited account_tax to add additional fields"""
    _inherit = 'account.tax'

    qbooks_tax = fields.Char(string='Tax ', help='Quickbook tax id', copy=False)
    qbooks_tax_rate = fields.Char(string='Tax Rate ID',
                                  help='Quickbook tax rate id', copy=False)
    qbooks_sync_token = fields.Char(string='Sync Token',
                                    help='Quickbook Synchronization token',
                                    copy=False)
    tax_agency_id = fields.Many2one('tax.agency',
                                    string="Tax Agency", required=True,
                                    help='The corresponding tax agency')
