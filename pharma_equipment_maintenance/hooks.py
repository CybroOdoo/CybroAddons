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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tools import SQL


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
                   WHEN r.state = 'done' THEN 'qa_verified'
                   WHEN s.id = %s THEN 'in_progress'
                   ELSE 'new' END
          FROM maintenance_stage s
         WHERE r.stage_id = s.id
           AND r.pharma_state = 'new'
           AND r.qa_verified_by IS NULL
    """, [env.ref('maintenance.stage_1').id])


def uninstall_hook(env):
    """Give back what the module changed outside itself.

    The Maintenance app menu is restricted to pharma roles while the module
    is installed; Odoo does not restore another module's record on
    uninstall, so its original group is set back here. The sterile switch
    implies its group into every internal user, which keeps the group from
    being removed with the module's data; it is removed here instead.
    """
    menu = env.ref('maintenance.menu_maintenance_title', raise_if_not_found=False)
    regular = env.ref('base.group_user_regular', raise_if_not_found=False)
    if menu and regular:
        menu.sudo().group_ids = [(6, 0, regular.ids)]
    sterile = env.ref('pharma_equipment_maintenance.group_pharma_sterile_mfg',
                      raise_if_not_found=False)
    if sterile:
        # The ORM refuses to delete a group behind a settings toggle, and this
        # module's toggle is still loaded while the module is removed, so the
        # group would outlive it. Its user, menu and implication links cascade.
        env.cr.execute(SQL('DELETE FROM res_groups WHERE id = %s', sterile.id))
        env.invalidate_all()
