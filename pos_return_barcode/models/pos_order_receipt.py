###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from urllib.parse import quote

from odoo import models
from odoo.tools.image import image_data_uri


class PosOrderReceipts(models.AbstractModel):
    _inherit = "pos.order.receipt"

    def order_receipt_generate_data(self, basic_receipt=False):
        data = super().order_receipt_generate_data(basic_receipt)
        barcode = self.barcode
        if not barcode and self.pos_reference:
            barcode = (
                self.pos_reference.replace("Order", "")
                .replace(" ", "")
                .replace("-", "")
                .strip()
            )
        if barcode:
            data["image"]["pos_barcode"] = barcode
            try:
                barcode_png = self.env["ir.actions.report"].barcode(
                    "Code128",
                    barcode,
                    width=600,
                    height=100,
                    humanreadable=0,
                )
                data["image"]["pos_barcode_src"] = image_data_uri(barcode_png)
            except ValueError:
                base_url = self.env.company.get_base_url()
                data["image"]["pos_barcode_src"] = (
                    f"{base_url}/report/barcode/Code128/{quote(barcode)}"
                )

        return data
