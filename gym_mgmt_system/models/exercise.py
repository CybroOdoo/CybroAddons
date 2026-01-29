# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Shahul Faiz (<https://www.cybrosys.com>)
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

from odoo import api, fields, models, _
from odoo.addons.website.tools import get_video_embed_code
from odoo.exceptions import ValidationError


class GymExercises(models.Model):
    _name = "gym.exercise"
    _inherit = ["mail.thread", "mail.activity.mixin", "image.mixin"]
    _description = "Gym Exercises"
    _rec_name = "name"
    _columns = {

        'image': fields.Binary("Image", help="This field holds the image"),

    }

    name = fields.Char(string="Name")
    exercise_for_ids = fields.Many2many("exercise.for", string="Exercise For")
    equipment_ids = fields.Many2one('product.product', string='Equipment',
                                    required=True, tracking=True,
                                    domain="[('gym_product', '!=',False)]")
    note_benefit = fields.Html('Note')
    note_step = fields.Html('Note')
    embed_code = fields.Html(compute="_compute_embed_code", sanitize=False)
    video_url = fields.Char('Video URL',
                            help='URL of a video for showcasing your product.')
    image = fields.Binary("Image", help="This field holds the image")
    image12 = fields.Binary("Image", help="This field holds the image")
    image123 = fields.Binary("Image", help="This field holds the image")
    image124 = fields.Binary("Image", help="This field holds the image")

    @api.depends('video_url')
    def _compute_embed_code(self):
        """ to get video field """
        for image in self:
            image.embed_code = get_video_embed_code(image.video_url)

    @api.constrains('video_url')
    def _check_valid_video_url(self):
        """ check url is valid or not """
        for image in self:
            if image.video_url and not image.embed_code:
                raise ValidationError(
                    _("Provided video URL for '%s' is not valid. "
                      "Please enter a valid video URL.", image.name))
