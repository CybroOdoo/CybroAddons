# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import os
from datetime import datetime, timedelta
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import ImageProcess

mimetypes_global = ['image/avif',
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
                    'image/x-xwindowdump']


class ImageCompressor(models.Model):
    """
    A class for storing the Rules records used for attachments compression
    """
    _name = "ir.image.compressor.rule"
    _description = "ir_Image_Compressor_Rule"

    name = fields.Char(string="Name", required=True)
    af_model_ids = fields.Many2many("ir.model", string="Model(s)", required=True, help="Models where this rule applied")
    source_format_ids = fields.Many2many("source.file.format",
                                         string="Source Format", help="The file formats of attachments to which this rule is applied.")
    quality = fields.Integer(string="Quality", help="""Quality level of the compressed image in percentage. If left empty, 95% will be used as default value.
    - for JPEG: 1 is worse, 95 is best. Values above 95 should be
              avoided. Falsy values will fallback to 95, but only if the image
              was changed, otherwise the original image is returned.
            - for PNG: set falsy to prevent conversion to a WEB palette.
            - for other formats: no effect.""",)
    destination_format = fields.Selection([('JPEG', '.jpeg'),
                                           ('PNG', '.png'),
                                           ('GIF', '.gif'),
                                           ('ICO', '.ico')],
                                          string="Destination format",
                                          default='JPEG', required=True, help="The format to which the source files are converted or compressed.")
    active = fields.Boolean(string="Active", help="Whether the rule is active or inactive.")
    minimum_size = fields.Integer(string="Minimum Size(KB)", help="The minimum size of the attachment file in KB for the rule to be applied.")
    older_days = fields.Integer(string="Older than(days)", help="The age of the attachment in days for this rule to be applied.")
    allow_recompress = fields.Boolean("Recompress", default=False, help="Whether to compress already compressed attachments or not.")
    @api.constrains('account_type', 'reconcile')
    def _check_reconcile(self):
        for rule in self:
            if rule.quality and not (1 <= rule.quality <= 95) and rule.destination_format == 'jpeg':
                raise ValidationError(
                    _('The quality value should be between 1 and 95.'))


    def _get_attachments_domain(self, model_names):
        """ Method to generate dynamic domain based on the given rules """
        all_mime_types = \
            list(set(mimetypes_global).union(
                set(self.env['source.file.format'].sudo().
                    search([]).mapped('mime_type'))))
        if not self.source_format_ids:
            domains = [('mimetype', 'in', all_mime_types)]
        else:
            domains = [
                ('mimetype', 'in', self.source_format_ids.mapped('mime_type'))]
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
        if not self.allow_recompress:
            domains = expression.AND([domains, [('is_compressed', '=', False)]])
        return domains

    def _schedule_auto_compress(self):
        """ The scheduled action method for compressing or converting the attachment files.
        All converted files will replace the source files in the attachment to save storage space. """
        i_c_rules = self.env['ir.image.compressor.rule']. \
            search([('active', '=', True)])
        for record in i_c_rules:
            res_models = record.af_model_ids
            model_names = res_models.mapped('model')
            attach_ments = self.env['ir.attachment'].search(
                record._get_attachments_domain(model_names))
            for rec in attach_ments:
                if rec.raw:
                    img = ImageProcess(rec.raw,
                                       verify_resolution=False)
                else:
                    img = ImageProcess(base64.b64decode(rec.datas),
                                       verify_resolution=False)
                quality = int(record.quality if record.quality else 95)
                if record.destination_format:
                    image_data = img.image_quality(quality=quality, output_format=record.destination_format)
                else:
                    image_data = img.image_quality(quality=quality)
                if rec.raw:
                    rec.raw = image_data
                else:
                    rec.datas = base64.b64encode(image_data)
                if record.destination_format:
                    base = os.path.splitext(rec.name)[0]
                    rec.name = base + dict(record._fields['destination_format'].selection).get(record.destination_format)
