# -*- coding: utf-8 -*-
# Copyright 2019 Noviat NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo


def update_discount_product_value(env):
    discount_product = env.ref(
        'website_coupon.discount_product')
    discount_product.default_code = 'gift_coupon'


def migrate(cr, version):
    if not version:
        # installation of the module
        return
    with odoo.api.Environment.manage():
        env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
        update_discount_product_value(env)
