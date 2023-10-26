# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mruthul Raj (odoo@cybrosys.com)
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
###############################################################################
import re
from odoo import api, models


class IrAttachment(models.Model):
    """Class for the inherited  model of ir_attachment to add custom function
       chatter image."""
    _inherit = 'ir.attachment'

    @api.model
    def chatter_image(self, model, model_id, image):
        """ Create an attachment with the given image data and link it to the
            specified model.
            :param str model: Model name
            :param str model_id: ID of the record in the model
            :param str image: Image data URL
            :return boolean: Returns true."""
        attachment = self.create({
            'name': 'ChatterImage',
            'datas': re.sub('^data:image\/\w+;base64,', '', image),
            'mimetype': 'image/png',
            'type': 'binary',
            'index_content': 'image',
            'res_model': 'mail.compose.message'
        })
        self.env[model].browse(int(model_id)).message_post(
            message_type='comment',
            attachment_ids=[attachment.id]
        )
        return True
