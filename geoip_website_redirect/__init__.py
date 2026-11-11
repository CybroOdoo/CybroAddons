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
#############################################################################
from . import controllers
from . import models


def _post_init_hook(env):
    """Automatically ensure website pricelists exist for all active currencies and website country currencies."""
    website = env['website'].search([], limit=1)
    if not website:
        return

    # 1. Collect all currencies already active in Odoo
    currencies = env['res.currency'].search([('active', '=', True)])

    # 2. Dynamically collect currencies for company country and active languages
    company = env.company
    if company and company.currency_id:
        if not company.currency_id.active:
            company.currency_id.write({'active': True})
        currencies |= company.currency_id
    if company and company.country_id and company.country_id.currency_id:
        if not company.country_id.currency_id.active:
            company.country_id.currency_id.write({'active': True})
        currencies |= company.country_id.currency_id

    # 3. Dynamically collect currencies for all countries linked to installed website and system languages
    langs = website.language_ids | env['res.lang'].search([('active', '=', True)])
    for lang in langs:
        if '_' in (lang.code or ''):
            country_code = lang.code.split('_')[-1]
            country = env['res.country'].search([('code', '=ilike', country_code)], limit=1)
            if country and country.currency_id:
                if not country.currency_id.active:
                    country.currency_id.write({'active': True})
                currencies |= country.currency_id

    # 4. Ensure a website pricelist exists for each dynamically detected currency
    for curr in currencies:
        existing_pl = env['product.pricelist'].search([
            ('currency_id', '=', curr.id),
            '|', ('website_id', '=', website.id),
            ('website_id', '=', False),
        ], limit=1)
        if not existing_pl:
            env['product.pricelist'].create({
                'name': f'{curr.name} Pricelist',
                'currency_id': curr.id,
                'website_id': website.id,
                'selectable': True,
            })
