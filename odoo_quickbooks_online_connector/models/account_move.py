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


class AccountMove(models.Model):
    """Inherited account_move to add additional fields for QuickBooks
    integration"""
    _inherit = 'account.move'

    qbooks_invoice = fields.Char(string='Invoice ID',
                                 help='ID of the sale invoice comes from'
                                      ' Quickbook', copy=False)
    qbooks_bill = fields.Char(string='Bill ID', help='Quickbook bill id',
                              copy=False)
    qbooks_credit = fields.Char(string='Credit Note ID',
                                help='ID of the Credit Note  comes from'
                                     ' Quickbook', copy=False)
    qbooks_refund = fields.Char(string='Refund ID',
                                help='ID of the Refund  comes from'
                                     ' Quickbook', copy=False)
    qbooks_sync_token = fields.Char(string='Sync Token',
                                    help='Quickbook Synchronization token',
                                    copy=False)
