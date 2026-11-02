# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo.tests import HttpCase, tagged

from odoo.addons.sale_stock.tests.common import TestSaleStockCommon


@tagged('post_install', '-at_install')
class TestSaleReturnTour(TestSaleStockCommon, HttpCase):
    """Drive the rewritten SaleReturn Interaction in headless Chrome."""

    def test_return_modal_interaction(self):
        self.warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        partner = self.env['res.partner'].create({'name': 'Tour Portal User'})
        self.env['res.users'].create({
            'name': 'Tour Portal User',
            'login': 'return_tour_user',
            'password': 'return_tour_user',
            'partner_id': partner.id,
            'group_ids': [(6, 0, [self.env.ref('base.group_portal').id])],
        })
        order = self._so_deliver(self.product, quantity=2, partner=partner)
        self.start_tour(
            order.get_portal_url(), 'website_return_management_tour',
            login='return_tour_user')
