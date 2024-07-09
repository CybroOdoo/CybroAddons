# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class XtreamTestimonials(models.Model):
    """
    Model for testimonials
    """
    _name = 'xtream.testimonials'
    _description = "Xtream Testimonials"

    partner_id = fields.Many2one("res.partner", required=True,
                                 help="Select the customer providing the"
                                      "testimony",
                                 domain="[('is_company', '=', False)]")
    testimony = fields.Text(string="Testimony", required=True,
                            help="Enter the testimonial provided by the"
                                 "customer")
