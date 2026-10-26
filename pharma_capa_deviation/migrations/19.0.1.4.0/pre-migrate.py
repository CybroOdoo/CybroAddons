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
"""Hand the preventive action's stored data over to pharma_capa_preventive.

The recurring checks and the fields the preventive engine stores now belong
to the pharma_capa_preventive add-on. Their ownership is moved before this
module is updated: otherwise the update would drop the columns and the
pharma_capa_check table it no longer defines. The data then survives until
the add-on is installed — or stays untouched if it never is.

The views that moved are deleted here, before any module loads: they
extend forms of other models (manufacturing orders) with fields that no longer
exist, and a module loaded later would fail to validate those forms. Menus,
actions, the cron and access rules are left with this module so the update
removes them at its end; the add-on brings its own.
"""
import logging

_logger = logging.getLogger(__name__)

NEW_MODULE = 'pharma_capa_preventive'
# Stored fields that move, as (model table name, field name).
STORED_FIELDS = [
    ('pharma_capa', 'restarted_on'),
    ('pharma_deviation', 'source_capa_id'),
    ('pharma_deviation', 'source_capa_check_id'),
    ('pharma_qc_test_order', 'capa_check_id'),
    ('pharma_qc_test_order', 'capa_check_capa_id'),
    ('mrp_production', 'pharma_under_surveillance'),
]
# Views now carried by the add-on.
MOVED_VIEWS = [
    'mrp_production_form_pharma_surveillance',
    'mrp_production_list_pharma_surveillance',
    'pharma_capa_check_form',
    'pharma_capa_check_list',
    'pharma_capa_check_search',
    'pharma_capa_restart_wizard_form',
]


def migrate(cr, version):
    if not version:
        return
    names = ['field_%s__%s' % field for field in STORED_FIELDS]
    cr.execute("""
        UPDATE ir_model_data
           SET module = %s
         WHERE module = 'pharma_capa_deviation'
           AND (
                (model = 'ir.model' AND name = 'model_pharma_capa_check')
             OR (model = 'ir.model.fields'
                 AND (name LIKE 'field\\_pharma\\_capa\\_check\\_\\_%%'
                      OR name = ANY(%s)))
             OR (model = 'ir.model.fields.selection'
                 AND name LIKE 'selection\\_\\_pharma\\_capa\\_check\\_\\_%%')
           )
    """, (NEW_MODULE, names))
    _logger.info('Handed %s records of the preventive action over to %s.',
                 cr.rowcount, NEW_MODULE)
    cr.execute("""
        DELETE FROM ir_ui_view
         WHERE id IN (SELECT res_id FROM ir_model_data
                       WHERE module = 'pharma_capa_deviation'
                         AND model = 'ir.ui.view' AND name = ANY(%s))
    """, (MOVED_VIEWS,))
    cr.execute("""
        DELETE FROM ir_model_data
         WHERE module = 'pharma_capa_deviation'
           AND model = 'ir.ui.view' AND name = ANY(%s)
    """, (MOVED_VIEWS,))
