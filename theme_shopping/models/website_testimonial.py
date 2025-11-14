# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models,fields


class WebsiteTestimonial(models.Model):
    """ Class for adding testimonials theme shopping"""
    _name = 'website.testimonial'
    _description = 'Testimonial Review'
    _inherit = 'mail.thread'
    _rec_name ='user_id'

    user_id = fields.Many2one('res.users', required=True,string='User Name')
    testimonial = fields.Text('Testimonial', required=True)
    image = fields.Binary()  # To store the user's image, if you want to allow image uploads

    @api.onchange('user_id')
    def _onchange_name(self):
        """ For setting profile picture while changing the user """
        if self.user_id and self.user_id.image_1920:
            self.image = self.user_id.image_1920
        else:
            self.image = False
