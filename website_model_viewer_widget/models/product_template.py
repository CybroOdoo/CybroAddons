# pylint: disable=unknown-option-value
# pylint: disable=missing-module-docstring
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
import binascii

from odoo import api, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Inherit product.template to validate 3D model file format."""
    _inherit = 'product.template'

    @api.constrains('model_3d')
    def _check_model_3d(self):
        """Basic check for GLB magic bytes 'glTF'."""
        for record in self:
            if record.model_3d:
                data = bytes(record.model_3d)
                if not data.startswith(b'glTF'):
                    try:
                        data = base64.b64decode(data)
                    except (ValueError, binascii.Error):
                        data = b''
                if not data.startswith(b'glTF'):
                    msg = self.env._(
                        "Invalid file format. Please upload a valid 3D model "
                        "(.glb).",
                    )
                    raise ValidationError(msg)
