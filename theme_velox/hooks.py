# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
import logging
import datetime

_logger = logging.getLogger(__name__)

"""List of demo products and quantities for the Trending Now snippet."""
TRENDING_DEMO_ORDERS = [
    ('velox_prod_phantom_x',    12),
    ('velox_prod_court_master', 10),
    ('velox_prod_aeroknit',      9),
    ('velox_prod_jumpmaster',    8),
    ('velox_prod_soccer_shoes',  7),
    ('velox_prod_basketball',    6),
    ('velox_prod_tech_fleece',   3),
    ('velox_prod_yoga_leggings', 2),
    ('velox_prod_core_tshirt',   2),
]


def post_init_hook(env):
    """
    Called automatically by Odoo after the module finishes installing.
    Creates confirmed sale orders with demo quantities so the Trending Now
    snippet can rank products by units sold this month.

    Odoo 18 note: the hook signature is ``post_init_hook(env)`` — the older
    ``post_init_hook(cr, registry)`` form is still accepted but deprecated.
    """
    _logger.info("Velox: seeding demo trending sale orders…")

    partner = env.ref('base.res_partner_1', raise_if_not_found=False)
    if not partner:
        partner = env['res.partner'].sudo().search(
            [('customer_rank', '>', 0)], limit=1
        )
    if not partner:
        partner = env.ref('base.partner_root')

    order_date = datetime.datetime.now().replace(
        day=1, hour=10, minute=0, second=0, microsecond=0
    )

    created = 0
    for xmlid_suffix, qty in TRENDING_DEMO_ORDERS:
        try:
            tmpl = env.ref(
                f'theme_velox.{xmlid_suffix}', raise_if_not_found=False
            )
            if not tmpl:
                _logger.warning("Velox: %s not found, skipping", xmlid_suffix)
                continue

            product = tmpl.product_variant_ids[:1]
            if not product:
                _logger.warning(
                    "Velox: no variant for %s, skipping", xmlid_suffix
                )
                continue

            order = env['sale.order'].sudo().create({
                'partner_id': partner.id,
                'date_order': order_date,
                'state': 'draft',
                'order_line': [(0, 0, {
                    'product_id':       product.id,
                    'product_uom_qty':  qty,
                    'price_unit':       tmpl.list_price,
                    'name':             tmpl.name,
                })],
            })
            order.sudo().action_confirm()
            order.sudo().action_lock()
            created += 1
        except Exception as exc:
            _logger.warning(
                "Velox: could not create demo order for %s: %s",
                xmlid_suffix, exc
            )

    _logger.info(
        "Velox: demo trending orders done (%d/%d created).",
        created, len(TRENDING_DEMO_ORDERS)
    )
