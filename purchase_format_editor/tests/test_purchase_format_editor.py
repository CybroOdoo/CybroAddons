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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestPurchaseFormatEditor(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.layout = cls.env['doc.layout.purchase'].create({
            'name': 'Test Layout',
            'base_color': '#000000',
        })
        cls.company = cls.env.company
        cls.company.write({
            'base_layout_purchase': 'default',
            'document_layout_purchase_id': cls.layout.id,
        })
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.env.ref('base.res_partner_1').id,
        })

    def test_related_fields(self):
        """Test related fields in purchase order."""
        self.assertEqual(
            self.purchase_order.theme_id_purchase,
            self.layout
        )
        self.assertEqual(
            self.purchase_order.company_id.base_layout_purchase,
            'default'
        )

    def test_print_pdf_action(self):
        """Test PDF preview action."""
        wizard = self.env['base.document.layout'].create({
            'company_id': self.company.id,
        })
        action = wizard.print_pdf()
        self.assertEqual(
            action['type'],
            'ir.actions.act_url'
        )
        self.assertIn(
            '/purchase/pdf/preview',
            action['url']
        )