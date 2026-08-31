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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields

class CineverseMovie(models.Model):
    _name = 'cineverse.movie'
    _description = 'CineVerse Movie'
    _order = 'sequence, id'

    name = fields.Char(string='Movie Title', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    image = fields.Image(string='Poster Image', max_width=1024, max_height=1024)
    image_url = fields.Char(string='External Image URL', help="Fallback poster URL when no binary image is uploaded.")
    rating = fields.Float(string='Rating', default=9.0, digits=(3, 1))
    duration = fields.Char(string='Duration', default='2h 00m')
    category = fields.Char(string='Genre / Category', default='Sci-Fi')
    badge = fields.Char(string='Badge / Format', default='IMAX')
    showtimes = fields.Char(string='Showtimes', default='11:30, 14:15, 17:45, 21:00', help="Comma-separated screening times.")
    active = fields.Boolean(string='Active', default=True)

    def get_poster_url(self):
        self.ensure_one()
        if self.image:
            return f'/web/image/cineverse.movie/{self.id}/image'
        return self.image_url or 'https://images.unsplash.com/photo-1635805737707-575885ab0820?auto=format&fit=crop&w=500&q=80'
