# -*- coding: utf-8 -*-
#############################################################################
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
"""Move single-choice preventive scopes onto the three scope tag fields."""
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'pharma_capa' AND column_name = 'scope'
    """)
    if not cr.fetchone():
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute("""
        INSERT INTO pharma_capa_scope_product_rel (capa_id, product_tmpl_id)
        SELECT id, scope_product_id FROM pharma_capa
         WHERE scope = 'product' AND scope_product_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    cr.execute("""
        INSERT INTO pharma_capa_scope_workcenter_rel (capa_id, workcenter_id)
        SELECT id, scope_workcenter_id FROM pharma_capa
         WHERE scope = 'line' AND scope_workcenter_id IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    # "Affected batch only" no longer exists. Leaving the fields empty would
    # widen those actions to the whole site, so they take the batch's product.
    cr.execute("""
        SELECT c.id, pp.product_tmpl_id
          FROM pharma_capa c
          JOIN pharma_deviation d ON d.id = c.deviation_id
          LEFT JOIN mrp_production mo ON mo.id = d.batch_id
          LEFT JOIN stock_lot l ON l.id = d.lot_id
          LEFT JOIN product_product pp
                 ON pp.id = coalesce(mo.product_id, l.product_id)
         WHERE c.scope = 'batch'
    """)
    batch_scoped = cr.fetchall()
    for capa_id, tmpl_id in batch_scoped:
        if tmpl_id:
            cr.execute("""
                INSERT INTO pharma_capa_scope_product_rel
                       (capa_id, product_tmpl_id)
                VALUES (%s, %s) ON CONFLICT DO NOTHING
            """, (capa_id, tmpl_id))
    env.invalidate_all()
    capas = env['pharma.capa'].search([])
    env.add_to_compute(capas._fields['scope_site_wide'], capas)
    capas.flush_recordset()
    for capa in capas.browse([row[0] for row in batch_scoped]):
        capa.message_post(body=
            'Scope "Affected batch only" was retired. This action now watches '
            'batches of the source batch\'s product; review the scope.')
    # A batch trigger is now always a campaign.
    for capa in capas.filtered(lambda c: c.capa_type == 'preventive'
                               and c.trigger_type == 'batch'
                               and c.control_nature == 'permanent'):
        capa.control_nature = 'campaign'
        capa.message_post(body=
            'Test-triggered actions are now always campaigns; control '
            'nature changed from permanent to campaign. Use a time trigger '
            'for a control that continues indefinitely.')
