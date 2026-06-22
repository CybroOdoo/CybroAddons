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

from odoo import api, models
from odoo.exceptions import ValidationError
import base64


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('model_3d')
    def _check_model_3d(self):
        for record in self:
            if record.model_3d:
                # Basic check for GLB magic bytes 'glTF'
                decoded_data = base64.b64decode(record.model_3d)
                if not decoded_data.startswith(b'glTF'):
                    raise ValidationError("Invalid file format. Please upload a valid 3D model (.glb).")
