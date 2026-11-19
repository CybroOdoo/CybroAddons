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
#############################################################################
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_top_deal_product = fields.Boolean(
        string="Top Deal Product",
        help="Whether the product is included in the Top Deal carousel.",
    )
    offer_price = fields.Float(
        help="Discounted price displayed during the deal.",
    )
    time_period_from = fields.Date(
        string="From Date",
        help="First day on which the offer is visible.",
        default=fields.Date.today,
    )
    time_period_end = fields.Date(
        string="End Date",
        help="Last day on which the offer is visible.",
        default=fields.Date.today,
    )
    ready_to_top_deal = fields.Boolean(
        string="Ready to Top Deal",
        help="Whether the product is currently within its deal period.",
    )
    actual_price = fields.Monetary(
        help="Regular price saved when the product is enabled as a deal.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Save the normal price when a product is created as a deal."""
        default_price = self.default_get(['list_price']).get('list_price', 1.0)
        for vals in vals_list:
            if vals.get('is_top_deal_product') and 'actual_price' not in vals:
                vals['actual_price'] = vals.get('list_price', default_price)
        return super().create(vals_list)

    def write(self, vals):
        """Preserve each product's normal price when enabling a deal."""
        if vals.get('is_top_deal_product') and 'actual_price' not in vals:
            newly_enabled = self.filtered(
                lambda product: not product.is_top_deal_product,
            )
            remaining = self - newly_enabled
            if newly_enabled:
                for product in newly_enabled:
                    super(ProductTemplate, product).write(
                        {
                            **vals,
                            'actual_price': vals.get(
                                'list_price', product.list_price,
                            ),
                        },
                    )
            if remaining:
                return super(ProductTemplate, remaining).write(vals)
            return True
        if vals.get('is_top_deal_product') is False:
            currently_enabled = self.filtered('is_top_deal_product')
            remaining = self - currently_enabled
            for product in currently_enabled:
                super(ProductTemplate, product).write(
                    {
                        **vals,
                        'list_price': vals.get(
                            'list_price', product.actual_price or product.list_price,
                        ),
                        'compare_list_price': 0.0,
                        'ready_to_top_deal': False,
                    },
                )
            if remaining:
                return super(ProductTemplate, remaining).write(vals)
            return True
        return super().write(vals)

    def _get_combination_info(self, combination=False, product_id=False,
                              add_qty=1, uom_id=False, only_template=False,
                              pricelist=None, fiscal_position=None):
        """Return the variant info based on its combination.
        See `_get_combination_info` for more information.
        """
        combination_info = super()._get_combination_info(
            combination=combination, product_id=product_id, add_qty=add_qty,
            uom_id=uom_id, only_template=only_template,
            pricelist=pricelist, fiscal_position=fiscal_position)
        combination_info['offer_price'] = self.offer_price
        return combination_info

    @api.onchange('is_top_deal_product')
    def _onchange_is_top_deal_product(self):
        """Keep the regular price while a product is configured as a deal."""
        if self.is_top_deal_product:
            self.actual_price = self.list_price
            self.time_period_from = fields.Date.today()
            self.time_period_end = fields.Date.today()
        else:
            self.list_price = self.actual_price
            self.compare_list_price = 0.0
            self.ready_to_top_deal = False

    @api.constrains(
        'is_top_deal_product', 'time_period_from', 'time_period_end',
    )
    def _check_top_deal_period(self):
        for product in self:
            if (
                product.is_top_deal_product
                and product.time_period_from
                and product.time_period_end
                and product.time_period_from > product.time_period_end
            ):
                raise ValidationError(
                    self.env._("The deal start date must be before its end date."),
                )

    def check_top_deal(self):
        """Check the timeframe of the top deal offer."""
        if self:
            products = self.filtered('is_top_deal_product')
        else:
            products = self.search(
                [
                    ('is_top_deal_product', '=', True),
                    ('time_period_from', '!=', False),
                    ('time_period_end', '!=', False),
                ],
            )
        today = fields.Date.today()
        for product in products:
            if (
                product.time_period_from
                and product.time_period_end
                and product.time_period_from <= today <= product.time_period_end
            ):
                if product.offer_price < product.actual_price:
                    product.write(
                        {
                            'ready_to_top_deal': True,
                            'list_price': product.offer_price,
                            'compare_list_price': product.actual_price,
                        },
                    )
                else:
                    product.write(
                        {
                            'ready_to_top_deal': True,
                            'list_price': product.actual_price,
                            'compare_list_price': 0.0,
                        },
                    )
            else:
                product.write(
                    {
                        'ready_to_top_deal': False,
                        'list_price': product.actual_price,
                        'compare_list_price': 0.0,
                    },
                )

    def apply_top_deal_time(self):
        """Apply the configured deal period to the current product."""
        self.check_top_deal()
