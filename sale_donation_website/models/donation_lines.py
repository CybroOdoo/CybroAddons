## -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class DonationLines(models.Model):
    """Creating donation lines model."""
    _name = "donation.lines"
    _description = "Donation Lines"

    partner_id = fields.Many2one('res.partner',string="Partner",
                                 help="Partner name")
    sale = fields.Char(string="Sale", help="Sale order number")
    donation = fields.Many2one('donation.rule', string="Donation",
                               help="Name of the donation")
    date = fields.Datetime(string="Date", help="Date")
    donated_amount = fields.Float(string="Donated Amount",
                                  help="Donated Amount")
    website = fields.Many2one('website', string="Website", help="Website")
