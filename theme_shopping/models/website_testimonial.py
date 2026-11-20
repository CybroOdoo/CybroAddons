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
from odoo import api, fields, models


class WebsiteTestimonial(models.Model):
    """Store testimonials submitted through the website."""
    _name = 'website.testimonial'
    _description = 'Testimonial Review'
    _inherit = 'mail.thread'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users',
        required=True,
        string='User Name',
        help='User who submitted the testimonial.',
    )
    testimonial = fields.Text(
        required=True,
        help='Feedback displayed in the website testimonial snippet.',
    )
    image = fields.Binary(help='Profile image displayed with the testimonial.')

    @api.onchange('user_id')
    def _onchange_name(self):
        """Set the profile picture when the testimonial author changes."""
        if self.user_id and self.user_id.image_1920:
            self.image = self.user_id.image_1920
        else:
            self.image = False
