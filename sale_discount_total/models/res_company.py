#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from odoo import fields, models


class ResCompany(models.Model):
    """Add the sale discount approval settings on the company."""
    _inherit = 'res.company'

    so_double_validation = fields.Selection([
        ('one_step', 'Confirm sale orders in one step'),
        ('two_step', 'Get 2 levels of approvals to confirm a sale order'),
    ], string="Levels of Approvals", default='one_step',
        help="Ask for a manager approval when the discount exceeds the "
             "limit.")
    so_double_validation_limit = fields.Float(
        string="Discount Limit (%)",
        help="Discount percentage above which a sale order needs the "
             "approval of a manager.")
