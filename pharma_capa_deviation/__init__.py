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
from . import models


def post_init_hook(env):
    """Rebuild the audit-trail view so it captures deviation/CAPA changes."""
    if 'pharma.audit.trail' in env:
        env['pharma.audit.trail'].init()

def uninstall_hook(env):
    """Rebuild the audit-trail view without deviation/CAPA and purge their mail records."""
    if 'pharma.audit.trail' in env:
        env['pharma.audit.trail'].init(_excluded_tables={'pharma_deviation', 'pharma_capa'})

    orphan_models = ['pharma.capa', 'pharma.deviation']
    # Followers and activities reference the record by (res_model, res_id).
    env['mail.followers'].sudo().search(
        [('res_model', 'in', orphan_models)]).unlink()
    env['mail.activity'].sudo().search(
        [('res_model', 'in', orphan_models)]).unlink()
    # Deleting the messages cascades to their mail.notification and
    # mail.tracking.value rows (ondelete='cascade' on message_id).
    env['mail.message'].sudo().search(
        [('model', 'in', orphan_models)]).unlink()
