# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
from odoo import fields, models


class TenderDocument(models.Model):
    """Document attached to a tender for the vendors."""
    _name = "tender.document"
    _description = 'Tender Documents'

    name = fields.Char(help="Name of the document")
    attachment = fields.Binary(required=True,
                               help="Attachment related to the tender")
    filename = fields.Char(help="Original filename of the attachment")
    note = fields.Text(help="Notes related to the document")
    tender_id = fields.Many2one('tender.management', string="Tender Reference",
                                help='Tender the document belongs to.')
