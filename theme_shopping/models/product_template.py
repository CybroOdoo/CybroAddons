# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_top_deal_product = fields.Boolean(string="Top Deal Product",
                                         help="Whether the product is listed "
                                              "in the top deal product",
                                         store=True)
    offer_price = fields.Float(string="Offer Price",
                               help="Set an offer price to price to "
                                    "display on website")
    time_period_from = fields.Date(string="From Date",
                                   help="From date for offer price visibility",
                                   default=lambda self: fields.Date.today())
    time_period_end = fields.Date(string="End Date",
                                  help="End date for offer price visibility",
                                  default=lambda self: fields.Date.today())
    ready_to_top_deal = fields.Boolean(string="Ready to Top Deal",
                                       help="Determine whether the product is ready to be featured as a top deal.")
    actual_price = fields.Monetary(string="Actual Price")

    def _get_combination_info(self, combination=False, product_id=False,
                              add_qty=1, parent_combination=False,
                              only_template=False):
        """Return the variant info based on its combination.
        See `_get_combination_info` for more information.
        """
        combination_info = super()._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty,
            parent_combination=parent_combination, only_template=only_template)
        combination_info['offer_price'] = self.offer_price
        return combination_info

    @api.onchange('is_top_deal_product')
    def onchange_is_top_deal_product(self):
        """Set the offer price as new sale price and old sales price saves
         into new field """
        if self.is_top_deal_product:
            self.actual_price = self.list_price
            self.time_period_from = fields.Date.today()
            self.time_period_end = fields.Date.today()
            config = self.env['res.config.settings'].create(
                {'group_product_price_comparison': True})
            config.execute()
        else:
            self.list_price = self.actual_price
            self.compare_list_price = 0.0
            self.ready_to_top_deal = False

    def check_top_deal(self):
        """Check the timeframe of the top deal offer."""
        data = self.env['product.template'].search(
            [('is_top_deal_product', '=', 'True')])
        today = fields.Date.today()
        for rec in data:
            if today > rec.time_period_end:
                rec.write({'ready_to_top_deal': False,
                           'list_price': rec.actual_price,
                           'compare_list_price': 0.0
                           })

            elif rec.time_period_from <= today <= rec.time_period_end:
                if rec.offer_price < rec.actual_price:
                    rec.write({'ready_to_top_deal': True,
                               'list_price': rec.offer_price,
                               'compare_list_price': rec.actual_price})
                else:
                    rec.write({'ready_to_top_deal': True,
                               'list_price': rec.actual_price,
                               'compare_list_price': 0.0
                                })
            elif rec.time_period_from > rec.time_period_end:
                rec.write({'ready_to_top_deal': False})
                raise ValidationError("From date should be less than end date")
            else:
                rec.write({'ready_to_top_deal': False})

    def apply_top_deal_time(self):
        """Method for set time period for top deal products."""
        self.check_top_deal()
