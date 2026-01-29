# -*- coding: utf-8 -*-
###############################################################################
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
###############################################################################
import base64
from io import BytesIO
from odoo import api, fields, models

try:
    import qrcode
except ImportError:
    qrcode = None


class EventEventTicket(models.Model):
    """This class extends the 'event.event.ticket' model to include
    the generation of QR codes for event tickets."""
    _inherit = 'event.event.ticket'

    ticket_qr_code_image = fields.Binary(string='QRcode', attachment=False,
                                         help='QR code for Event Tickets.',
                                         readonly=True)

    @api.model
    def create(self, vals):
        """Generate qrcode when create new product."""
        res = super(EventEventTicket, self).create(vals)
        ean = self.generate_ticket_qr(res.id)
        res.ticket_qr_code_image = ean
        return res

    def generate_ticket_qr(self, val_id):
        """Action to generate QR code for Tickets.
        :param int val_id: id of the event.
        :return: event ticket qrcode image."""
        data = self.browse(val_id)
        if qrcode and base64:
            code = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3, border=4)
            code.add_data(f"Event: {data.event_id.name},")
            code.add_data(f"code: {data.event_id.id},")
            code.add_data(f"Ticket: {val_id},")
            code.add_data(f"Price: {data.price}")
            code.make(fit=True)
            img = code.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            return qr_image
