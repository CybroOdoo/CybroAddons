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
"""The follow-up email lists only the overdue invoices.

``data/mail_template_followup.xml`` is a ``noupdate`` file, so the upgrade
does not change the existing template. Replace its invoice loop
(``object.invoice_list`` -> ``object.overdue_invoice_ids``) in every
language; the rest of the template, customised or not, is kept.
"""
import logging

from psycopg2.extras import Json

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

OLD = 'object.invoice_list'
NEW = 'object.overdue_invoice_ids'


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    template = env.ref('base_accounting_kit.mail_template_followup',
                       raise_if_not_found=False)
    if not template:
        return
    cr.execute("SELECT body_html FROM mail_template WHERE id = %s",
               [template.id])
    bodies = cr.fetchone()[0] or {}
    changed = {lang: body.replace(OLD, NEW) for lang, body in bodies.items()
               if body and OLD in body}
    if changed:
        # Write the stored translations directly: works for every language
        # in the field, installed or not.
        cr.execute("UPDATE mail_template SET body_html = %s WHERE id = %s",
                   [Json(dict(bodies, **changed)), template.id])
        template.invalidate_recordset(['body_html'])
    _logger.info("Follow-up email template: invoice loop updated in %d "
                 "language(s).", len(changed))
