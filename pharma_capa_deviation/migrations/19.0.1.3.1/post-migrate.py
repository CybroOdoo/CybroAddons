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
"""Point the purchase page of this module's premium features at the pricing
page. The feature records are noupdate, so the data file alone does not
reach existing databases; a purchase page changed by hand is left alone."""

PRICING_URL = 'https://www.odoo.com/id_ID/pricing'
OLD_URL = 'https://apps.odoo.com/apps/modules/19.0/pharma_capa_deviation'


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE pharma_premium_feature
           SET purchase_url = %s
         WHERE module_name = %s
           AND (purchase_url IS NULL OR purchase_url = %s)
    """, (PRICING_URL, 'pharma_capa_deviation', OLD_URL))
