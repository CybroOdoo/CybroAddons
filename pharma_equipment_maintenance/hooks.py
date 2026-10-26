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
def post_init_hook(env):
    """Bring existing equipment and requests into the GMP register.

    Equipment numbered by ``_auto_init`` moves the sequence past its codes.
    Existing requests are given the pharma state matching their stage
    without changing the stage: closed history is shown as verified, since
    it was never QA verified in this system and cannot be now.
    """
    count = env['maintenance.equipment'].with_context(active_test=False).search_count([])
    sequence = env.ref('pharma_equipment_maintenance.seq_pharma_equipment', raise_if_not_found=False)
    if sequence and count:
        sequence.sudo().number_next_actual = count + 1
    env.cr.execute("""
        UPDATE maintenance_request r
           SET pharma_state = CASE
                   WHEN s.done THEN 'qa_verified'
                   WHEN s.id = %s THEN 'in_progress'
                   ELSE 'new' END
          FROM maintenance_stage s
         WHERE r.stage_id = s.id
           AND r.pharma_state = 'new'
           AND r.qa_verified_by IS NULL
    """, [env.ref('maintenance.stage_1').id])
