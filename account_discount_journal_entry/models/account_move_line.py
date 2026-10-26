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


class AccountMoveLine(models.Model):
    """Extends account.move.line to add a dedicated display_type and technical
    flag for category discount entries, preventing interference with Odoo's
    native discount allocation sync.
    """
    _inherit = 'account.move.line'

    display_type = fields.Selection(
        selection_add=[
            ('category_discount', 'Category Discount'),
        ],
        ondelete={'category_discount': 'cascade'},
    )
    is_discount_journal_entry = fields.Boolean(
        string="Is Discount Journal Entry",
        default=False,
        copy=False,
        help="Technical flag identifying lines created by account_discount_journal_entry.",
    )
