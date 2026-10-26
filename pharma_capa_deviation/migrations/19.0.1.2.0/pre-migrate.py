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
"""Carry CAPA data across the field simplification of 19.0.1.2.0.

Runs before the new fields are created: the old columns are still present.
"""


def _column_exists(cr, table, column):
    cr.execute("""
        SELECT 1 FROM information_schema.columns
         WHERE table_name = %s AND column_name = %s
    """, (table, column))
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return
    # A root cause typed on an existing CAPA was entered by hand; keep it as
    # an override so it is not replaced by the (new, empty) deviation field.
    cr.execute("""
        ALTER TABLE pharma_capa
        ADD COLUMN IF NOT EXISTS root_cause_overridden boolean
    """)
    cr.execute("""
        UPDATE pharma_capa
           SET root_cause_overridden = (coalesce(trim(root_cause), '') != '')
    """)
    # occurrence_target and batch_count merge into cycle_count.
    if _column_exists(cr, 'pharma_capa', 'batch_count'):
        cr.execute("""
            ALTER TABLE pharma_capa ADD COLUMN IF NOT EXISTS cycle_count integer
        """)
        cr.execute("""
            UPDATE pharma_capa
               SET cycle_count = CASE WHEN trigger_type = 'time'
                                      THEN occurrence_target
                                      ELSE batch_count END
        """)
    # The free-text effectiveness evidence becomes the QA conclusion; the
    # effectiveness field itself is now a computed summary.
    if _column_exists(cr, 'pharma_capa', 'effectiveness_check'):
        cr.execute("""
            ALTER TABLE pharma_capa
            ADD COLUMN IF NOT EXISTS effectiveness_conclusion varchar
        """)
        cr.execute("""
            UPDATE pharma_capa
               SET effectiveness_conclusion = effectiveness_check
             WHERE coalesce(trim(effectiveness_check), '') != ''
        """)
