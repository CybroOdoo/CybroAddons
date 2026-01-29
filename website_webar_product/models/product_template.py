# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """Extends the base product template model to include Augmented Reality
    (AR) features."""
    _inherit = 'product.template'

    enable_ar_images = fields.Boolean(string="Enable AR images",
                                      help="Enable to show AR images on the "
                                           "website.")
    ar_image_type = fields.Selection(selection=[("url", "Url"),
                                                ("upload", "Upload")],
                                     string="AR Image Type", default='url',
                                     help='Url:url of image.\n'
                                          'Upload:Upload image.')
    ar_url = fields.Char(string="Url for AR image",
                         help="Provide Valid Url for product AR Model.")
    model_ar = fields.Binary(string="AR Image", attachment=True,
                             help="Upload AR Image. Image should be glf/gltf "
                                  "format.")
    filename = fields.Char(string='File Name', required=True,
                           help="File name of uploaded file content.")
    poster_image = fields.Image(string="Poster Image",
                                help="Image used for carousal.")
    ar_scale = fields.Selection(
        selection=[("auto", "Auto"), ("fixed", "Fixed")], string="AR Scale",
        default='auto',
        help='Auto: allows the user from scaling the object in AR.\nFixed: is '
             'used to prevent the user from scaling the object in AR.')
    auto_rotate = fields.Boolean(string="Auto Rotate",
                                 help="Enables the auto-rotation of image.")
    ar_placement = fields.Selection(selection=[("floor", "Floor"),
                                               ("wall", "Wall")],
                                    string="AR Placement", default='floor',
                                    help='Floor : Place the object on floor.\n'
                                         'Wall: Place the object on wall.')

    @api.onchange('model_ar')
    def _onchange_model_ar(self):
        """Save Product AR model image as attachment."""
        if self.model_ar:
            if not self.filename.lower().endswith(('.glb', '.gltf')):
                raise UserError(
                    "Invalid file format. Please upload a GLB or GLTF file.")
            else:
                self.env['ir.attachment'].create({
                    'name':  self.filename,
                    'datas': self.model_ar,
                    'res_model': 'product.template',
                    'res_id': self._origin.id,
                })
