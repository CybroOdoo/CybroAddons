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

import base64
import logging
import os
from datetime import datetime, timedelta
from odoo import models, fields
from odoo.osv import expression
from odoo.tools import ImageProcess

_logger = logging.getLogger(__name__)

mimetypes_global = [
    'image/avif',
    'image/bmp',
    'image/gif',
    'image/ief',
    'image/jpeg',
    'image/jpeg',
    'image/jpeg',
    'image/heic',
    'image/heif',
    'image/png',
    'image/svg+xml',
    'image/tiff',
    'image/tiff',
    'image/vnd.microsoft.icon',
    'image/x-cmu-raster',
    'image/x-portable-anymap',
    'image/x-portable-bitmap',
    'image/x-portable-graymap',
    'image/x-portable-pixmap',
    'image/x-rgb',
    'image/x-xbitmap',
    'image/x-xpixmap',
    'image/x-ms-bmp',
    'image/x-xwindowdump'
]


class ImageCompressor(models.Model):
    """Model that defines rules for compressing image attachments.

    Each rule specifies the models, source formats, quality, destination
    format and filtering criteria (minimum size and age) used by the
    scheduled action to compress matching ``ir.attachment`` records.
    """
    _name = "ir.image.compressor.rule"
    _description = "ir_Image_Compressor_Rule"

    name = fields.Char(string="Name", required=True,
                       help="Name of the image compression rule.")
    af_model_ids = fields.Many2many(
        "ir.model", string="Model(s)", required=True,
        help="Select the models to which this compression rule applies.")
    source_format_ids = fields.Many2many(
        "source.file.format", string="Source Format",
        help="Specific source formats to compress.")
    quality = fields.Integer(
        string="Quality", help="Quality percentage of the compressed image.")
    destination_format = fields.Selection([
        ('JPEG', '.jpeg'),
        ('PNG', '.png'),
        ('GIF', '.gif'),
        ('ICO', '.ico')
    ], string="Destination format", default='JPEG', required=True,
        help="The target format for the compressed images.")
    active = fields.Boolean(
        string="Active", help="Archive or unarchive the rule.")
    minimum_size = fields.Integer(
        string="Minimum Size(KB)",
        help="Only compress images larger than this size in KB.")
    older_days = fields.Integer(
        string="Older than(days)",
        help="Only compress images older than this many days.")

    def _get_attachments_domain(self, model_names):
        """Build the search domain used to select attachments to compress.

        :param model_names: list of model names (``res_model``) to restrict
            the attachments to, as configured on the rule.
        :return: a search domain (list of tuples) combining the mime type,
            model, minimum size and age criteria of the current rule.
        """
        all_mime_types = list(set(mimetypes_global).union(
            set(self.env['source.file.format'].sudo().
                search([]).mapped('mime_type'))))

        if not self.source_format_ids:
            domains = [('mimetype', 'in', all_mime_types)]
        else:
            sr_fmts = self.source_format_ids.mapped('mime_type')
            domains = [('mimetype', 'in', sr_fmts)]

        if model_names:
            domains = expression.AND(
                [domains, [('res_model', 'in', model_names)]])

        if self.minimum_size:
            domains = expression.AND(
                [domains, [('file_size', '>', self.minimum_size * 1024)]])

        if self.older_days:
            old_day = datetime.now() + timedelta(days=-self.older_days)
            domains = expression.AND(
                [domains, [('create_date', '<', old_day)]])

        return domains

    def _schedule_auto_compress(self):
        """Compress the attachments matching every active rule.

        Invoked by the scheduled action, this iterates over all active
        compression rules, fetches the matching attachments and rewrites
        each one with a re-encoded image using the configured quality and
        destination format. Failures on individual attachments are logged
        and skipped so a single bad image does not stop the run.
        """
        i_c_rules = self.env['ir.image.compressor.rule'].\
            search([('active', '=', True)])

        for record in i_c_rules:
            res_models = record.af_model_ids
            model_names = res_models.mapped('model')
            attach_ments = self.env['ir.attachment'].search(
                record._get_attachments_domain(model_names))

            for rec in attach_ments:
                try:
                    if rec.raw:
                        img = ImageProcess(base64.b64encode(rec.raw), verify_resolution=False)
                    else:
                        if not rec.datas:
                            continue
                        img = ImageProcess(
                            rec.datas,
                            verify_resolution=False
                        )

                    quality = int(record.quality if record.quality else 95)

                    # Explicitly convert P mode images with transparency to RGBA 
                    # before Odoo's ImageProcess tries to save them.
                    if img.image and img.image.mode == 'P' and 'transparency' in img.image.info:
                        img.image = img.image.convert('RGBA')

                    if record.destination_format:
                        image_data = img.image_quality(
                            quality=quality,
                            output_format=record.destination_format
                        )
                    else:
                        image_data = img.image_quality(quality=quality)

                    if rec.raw:
                        rec.raw = image_data
                    else:
                        rec.datas = base64.b64encode(image_data)

                    if record.destination_format:
                        base = os.path.splitext(rec.name)[0]
                        dest_format_sel = dict(
                            record._fields['destination_format'].selection
                        )
                        rec.name = base + dest_format_sel.get(
                            record.destination_format
                        )
                except Exception as e:
                    _logger.warning(
                        "Failed to compress image attachment %s: %s",
                        rec.id, str(e)
                    )
                    continue
