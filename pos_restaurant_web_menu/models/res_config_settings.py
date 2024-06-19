# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from io import BytesIO
from odoo import fields, models, _
from odoo.exceptions import UserError
try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None


class ResConfigSettings(models.TransientModel):
    """Add new fields to configuration settings for viewing web menu for
    pos restaurant."""
    _inherit = 'res.config.settings'

    pos_restaurant_web_menu_view_mode = fields.Boolean(
        string="Pos Web Menu",
        help="Allow customers to view the menu on their phones.",
        related='pos_config_id.web_menu_view_mode', readonly=False)
    pos_web_qr_code = fields.Binary(
        string='QR code', related='pos_config_id.web_qr_code', readonly=False,
        help='Qr code of POS App that allows customers to view the menu on '
             'their smartphone.')

    def generate_table_qr_code(self):
        """Generate qr code on pos order having details of order in
        current session"""
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        session_id = self.pos_config_id.current_session_id.id
        if qrcode and base64 and session_id:
            qr = qrcode.QRCode(
                version=3,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=4, )
            qr.add_data(base_url + self.pos_config_id._get_web_menu_route())
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            self.write({'pos_web_qr_code': qr_image})
        else:
            raise UserError(
                _('Necessary Requirements To Run This Operation Is Not '
                  'Satisfied.Please open new session.'))
        data = {'image': self.pos_web_qr_code,
                'company': self.env.company.name}
        report_action = self.env.ref(
            'pos_restaurant_web_menu.'
            'pos_restaurant_web_menu_qr_code').report_action(self, data=data)
        return report_action
