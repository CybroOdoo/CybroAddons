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
"""Point the Preventive Action feature at its add-on module and Apps page.
The record is noupdate, so the data file alone does not reach existing
databases."""


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE pharma_premium_feature
           SET module_name = 'pharma_capa_preventive',
               purchase_url = 'https://apps.odoo.com/apps/modules/19.0/pharma_capa_preventive'
         WHERE code = 'capa_preventive'
    """)
