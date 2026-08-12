# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from datetime import date
from itertools import groupby
from operator import itemgetter
from odoo import models


class ProductProduct(models.Model):
    """Extend POS product information with pricelist and supplier data."""
    _inherit = "product.product"

    def get_product_info_pos(self, price, quantity, pos_config_id):
        """Extend POS product information with pricelist and supplier details."""
        res = super().get_product_info_pos(price, quantity, pos_config_id)
        config = self.env["pos.config"].browse(pos_config_id)
        pricelists = (
            config.available_pricelist_ids if config.use_pricelist else config.pricelist_id
        )
        price_per_pricelist_id = pricelists._price_get(self, quantity) if pricelists else {}
        res["pricelists"] = [
            {
                "id": pricelist.id,
                "name": pricelist.name,
                "price": price_per_pricelist_id[pricelist.id],
                "currency_id": pricelist.currency_id.id,
            }
            for pricelist in pricelists
        ]
        key = itemgetter("partner_id")
        supplier_list = []
        for key, group in groupby(sorted(self.seller_ids, key=key), key=key):
            for supplierinfo in list(group):
                if not (
                    (supplierinfo.date_start and supplierinfo.date_start > date.today())
                    or (supplierinfo.date_end and supplierinfo.date_end < date.today())
                    or (supplierinfo.min_qty > quantity)
                ):
                    supplier_list.append(
                        {
                            "id": supplierinfo.id,
                            "name": supplierinfo.partner_id.name,
                            "delay": supplierinfo.delay,
                            "price": supplierinfo.price,
                            "currency_id": supplierinfo.currency_id.id,
                        }
                    )
                    break
        res["suppliers"] = supplier_list
        return res
