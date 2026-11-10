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
#############################################################################
from odoo import api, models
from odoo.fields import Domain


class ProductTemplate(models.Model):
    """ Inherit product.template to filter pricelist rules on the Prices tab,
    showing only rules for pricelists marked with 'display_pricelist'. """
    _inherit = 'product.template'

    def _domain_pricelist_rule_ids(self):
        domain = super()._domain_pricelist_rule_ids()
        return domain & (
            Domain('pricelist_id', '=', False)
            | Domain('pricelist_id.display_pricelist', '=', True)
        )

    @api.model
    def _domain_fixed_pricelist_rule_ids(self):
        domain = super()._domain_fixed_pricelist_rule_ids()
        return domain & (
            Domain('pricelist_id', '=', False)
            | Domain('pricelist_id.display_pricelist', '=', True)
        )
