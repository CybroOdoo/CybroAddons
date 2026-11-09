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
"""Franchise Dealer Agreement Model"""
from odoo import fields, models


class FranchiseAgreement(models.Model):
    """Franchise Agreement Model."""
    _name = "franchise.agreement"
    _description = "Franchise Agreement Type."
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "agreement_type"

    agreement_type = fields.Selection(
        [('Monthly', 'Monthly'), ('Yearly', 'Yearly')],
        help='Franchise Agreement type', required=True)
    agreement_body = fields.Html(translate=True,
                                 help='Franchise Agreement contents',
                                 prefetch=True, sanitize=False)
