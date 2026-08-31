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


class AccountMoveLine(models.Model):
    """Inherited account_move_line to add additional fields for QuickBooks
    integration"""
    _inherit = 'account.move.line'

    qbooks_invoice = fields.Char(string='Invoice ID',
                                 help='ID of the sale invoice comes from'
                                      ' Quickbook', copy=False)
    qbooks_bill = fields.Char(string='Bill ID',
                              help='ID of the bill comes from Quickbook ',
                              copy=False)
    qbooks_sale = fields.Char(string='Sale ID',
                              help='ID of the sale  comes from Quickbook',
                              copy=False)
    qbooks_purchase = fields.Char(string='Purchase ID',
                                  help='ID of the purchase comes from Quickbook',
                                  copy=False)
    qbooks_payment = fields.Char(string='Payment ID',
                                 help='ID of the sale payment comes '
                                      'from Quickbook', copy=False)
    qbooks_invoice_line = fields.Char(string='Line ID',
                                      help='ID of the  invoice line comes '
                                           'from Quickbook', copy=False)
