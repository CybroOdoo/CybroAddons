# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class ImageCapture(models.TransientModel):
    """A class for capturing images"""
    _name = 'image.capture'
    _description = 'Image Captures'

    name = fields.Char(string='Name', help='Name of the image to capture')
    model_name = fields.Char(string='Model Name',
                             help="For getting the model name details")
    record_id = fields.Char(string='Record ID',
                            help="For getting the record ID details")
    field_name = fields.Char(string='Field Name',
                             help="Field name for uploading the image")

    def action_save_image(self, data, url):
        """
        Saving the images to corresponding models
        :param dict data: dictionary representing the details of fields.
        :param url: Image details.
        """
        image = url.split(',')
        self.env[data['model_name']].browse(
            int(data['record_id'])).sudo().write(
            {data['field_name']: image[1]})
