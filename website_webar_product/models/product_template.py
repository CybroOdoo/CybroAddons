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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """Extends product template to include Augmented Reality (AR) features."""

    _inherit = 'product.template'

    enable_ar_images = fields.Boolean(
        string="Enable AR Images",
        help="Enable to show AR images on the website."
    )
    ar_image_type = fields.Selection(
        selection=[("url", "URL"), ("upload", "Upload")],
        string="AR Image Type",
        default='url',
        help="URL: provide a URL for the 3D model.\n"
             "Upload: upload a 3D model file."
    )
    ar_url = fields.Char(
        string="URL for AR Image",
        help="Provide a valid URL for the product AR model."
    )
    model_ar = fields.Binary(
        string="AR Image",
        attachment=True,
        help="Upload AR image in GLB or GLTF format."
    )
    filename = fields.Char(
        string="File Name",
        help="File name of the uploaded 3D model content."
    )
    poster_image = fields.Image(
        string="Poster Image",
        help="Image used for carousel placeholder."
    )
    ar_scale = fields.Selection(
        selection=[("auto", "Auto"), ("fixed", "Fixed")],
        string="AR Scale",
        default='auto',
        help="Auto: allows the user to scale the object in AR.\n"
             "Fixed: prevents the user from scaling the object in AR."
    )
    auto_rotate = fields.Boolean(
        string="Auto Rotate",
        help="Enables automatic rotation of the 3D model."
    )
    ar_placement = fields.Selection(
        selection=[("floor", "Floor"), ("wall", "Wall")],
        string="AR Placement",
        default='floor',
        help="Floor: place the object on the floor.\n"
             "Wall: place the object on the wall."
    )

    @api.constrains('model_ar', 'filename')
    def _check_model_ar_format(self):
        """Validate uploaded 3D model file extension."""
        for record in self:
            if record.model_ar and record.filename:
                if not record.filename.lower().endswith(('.glb', '.gltf')):
                    raise UserError(record.env._(
                        "Invalid file format. Please upload a GLB or GLTF file."
                    ))

    @api.onchange('model_ar', 'filename')
    def _onchange_model_ar(self):
        """Provide instant client validation for uploaded 3D model."""
        if self.model_ar and self.filename:
            if not self.filename.lower().endswith(('.glb', '.gltf')):
                raise UserError(self.env._(
                    "Invalid file format. Please upload a GLB or GLTF file."
                ))
