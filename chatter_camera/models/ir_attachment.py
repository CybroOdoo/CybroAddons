# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
#
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, models


class IrAttachment(models.Model):
    """
    Extended model for attachments to add custom function chatter image.
    """
    _inherit = 'ir.attachment'

    @api.model
    def chatter_image(self, model, model_id, image):
        """
        Create an attachment with the given image data and link it to the
         specified model.
        model: Model name
        model_id: ID of the record in the model
        image: Image data URL
        return: True if successful
        """
        attachment = self.create([{
            'name': 'ChatterImage',
            'datas': image,
            'mimetype': 'image/png',
            'type': 'binary',
            'index_content': 'image',
            'res_model': 'mail.compose.message'
        }])
        self.env[model].browse(int(model_id)).message_post(
            message_type='comment',
            attachment_ids=[attachment.id]
        )
        return True
