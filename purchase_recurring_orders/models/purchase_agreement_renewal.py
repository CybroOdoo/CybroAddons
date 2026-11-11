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


class PurchaseAgreementRenewal(models.Model):
    """Renew purchase recurring agreement"""
    _name = 'purchase.agreement.renewal'
    _description = "Purchase Agreement Renewal"

    recurring_agreement_id = fields.Many2one('purchase.recurring.agreement',
                                             string='Agreement Reference',
                                             help="Reference of the agreement",
                                             ondelete='cascade')
    date = fields.Datetime(help="Date of the Renewal")
    comments = fields.Char(
        size=200, help='Renewal comments')
