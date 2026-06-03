# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
from odoo import fields, models

class TenderDocument(models.Model):
    """ Class for holding tender documents details. """
    _name = "tender.document"
    _description = 'Tender Documents'

    name = fields.Char(string="Name", help="Name of the document")
    attachment = fields.Binary(string="Attachment", required=True,
                               help="Attachment related to the tender")
    filename = fields.Char(string="Filename", help="Original filename of the attachment")
    note = fields.Text(string="Note", help="Notes related to the document")
    tender_id = fields.Many2one('tender.management', string="Tender Reference",help='related tender')
