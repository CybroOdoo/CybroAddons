# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models


class MultipleInvoice(models.Model):
    """Multiple Invoice Model"""
    _name = "multiple.invoice"
    _order = "sequence"

    sequence = fields.Integer(string='Sequence No')
    copy_name = fields.Char(string='Invoice Copy Name')
    journal_id = fields.Many2one('account.journal', string="Journal")


class AccountJournal(models.Model):
    """Inheriting Account Journal Model"""
    _inherit = "account.journal"

    multiple_invoice_ids = fields.One2many('multiple.invoice', 'journal_id',
                                           string='Multiple Invoice')
    multiple_invoice_type = fields.Selection(
        [('text', 'Text'), ('watermark', 'Watermark')], required=True,
        default='text', string="Display Type")
    text_position = fields.Selection([
        ('header', 'Header'),
        ('footer', 'Footer'),
        ('body', 'Document Body')
    ], required=True, default='header')
    body_text_position = fields.Selection([
        ('tl', 'Top Left'),
        ('tr', 'Top Right'),
        ('bl', 'Bottom Left'),
        ('br', 'Bottom Right'),
    ], default='tl')
    text_align = fields.Selection([
        ('right', 'Right'),
        ('left', 'Left'),
        ('center', 'Center'),
    ], default='right')
    layout = fields.Char(related="company_id.external_report_layout_id.key")
