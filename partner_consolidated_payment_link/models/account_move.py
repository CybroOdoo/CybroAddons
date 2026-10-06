# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1). It is forbidden to publish, distribute, sublicense, or sell
#    copies of the Software or modified copies of the Software.
#
#    The above copyright notice and this permission notice must be included in
#    all copies or substantial portions of the Software.
#
#############################################################################

from odoo import fields, models

class AccountMove(models.Model):
    """
    Inherit account.move to add fields for storing the consolidated payment
    link reference and tracking matched payments.
    """
    _inherit = "account.move"

    consolidated_payment_link_ref = fields.Char(
        string='Consolidated Payment Link Reference',
        copy=False,
        help="The reference to be set on journal items for identifying them for reconciling the entire due amount.",
        readonly=True,
    )
    matched_payment_ids = fields.Many2many(
        comodel_name='account.payment',
        relation='account_move_payment_rel',
        column1='move_id',
        column2='payment_id',
        string='Matched Payments',
        copy=False,
        help="Payments that have been matched to this invoice via the consolidated payment link.",
    )
