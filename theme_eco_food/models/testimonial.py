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
"""Customer testimonial model for the Eco Food theme."""

from odoo import fields, models


class Testimonial(models.Model):  # pylint: disable=abstract-method
    """Store customer reviews displayed in the testimonial snippet."""

    _name = "ecofood.testimonial"
    _description = "Testimonials"
    _rec_name = "partner_id"

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        help="Customer of the testimonial",
    )
    review = fields.Text(help="Add your review here")
