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


class ResPartner(models.Model):
    """Vendor details used by the tender management."""
    _inherit = 'res.partner'

    is_vendor = fields.Boolean(help="The partner takes part in tenders as a vendor.")
    tender_category_ids = fields.Many2many(
        'tender.category', string="Tender Categories",
        help="Tender categories the vendor registered for.")
    registered_tenders_ids = fields.Many2many(
        'tender.management',
        help="Tenders the vendor submitted a bid for.")
