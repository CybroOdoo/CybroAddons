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
from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestTextileAccess(TransactionCase):
    """Test the app as real users, who are not administrators."""

    @classmethod
    def setUpClass(cls):
        """Create a user per role, and a customer and vendor with orders."""
        super().setUpClass()
        cls.employee = new_test_user(cls.env, login='textile_employee',
                                     groups='base.group_user')
        cls.salesman = new_test_user(
            cls.env, login='textile_salesman',
            groups='sales_team.group_sale_salesman_all_leads')
        cls.sales_manager = new_test_user(
            cls.env, login='textile_sales_manager',
            groups='sales_team.group_sale_manager')
        cls.buyer = new_test_user(cls.env, login='textile_buyer',
                                  groups='purchase.group_purchase_user')
        cls.partner = cls.env['res.partner'].create({'name': 'Weaver'})
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id, 'is_textile_sale_order': True})
        cls.purchase_order = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id, 'is_textile_purchase_order': True})
        cls.inquiry = cls.env['website.inquiry'].create(
            {'inquirer': 'Jane Doe', 'email': 'jane@example.com'})

    def _menus(self, user):
        """Names of the Textile Management menus ``user`` can see."""
        root = self.env.ref('textile_management.textile_management_menu_root')
        menus = self.env['ir.ui.menu'].with_user(user)
        visible = menus.browse(menus._visible_menu_ids())
        return visible.filtered_domain(
            [('id', 'child_of', root.id)]).mapped('name')

    def test_01_report_as_salesman(self):
        """A salesman chooses from the customers, without purchase access."""
        wizard = self.env['textile.report'].with_user(self.salesman).create(
            {'type': 'customer'})
        self.assertIn(self.partner, wizard.textile_customer_ids)
        self.assertFalse(wizard.textile_vendor_ids)

    def test_02_report_as_buyer(self):
        """A buyer chooses from the vendors, without sales access."""
        wizard = self.env['textile.report'].with_user(self.buyer).create(
            {'type': 'vendor'})
        self.assertIn(self.partner, wizard.textile_vendor_ids)
        self.assertFalse(wizard.textile_customer_ids)

    def test_03_salesman_processes_inquiries(self):
        """Sales users move the inquiries through their stages."""
        inquiry = self.inquiry.with_user(self.salesman)
        inquiry.action_verified()
        inquiry.action_replied()
        self.assertEqual(inquiry.state, 'replied')
        with self.assertRaises(AccessError):
            inquiry.unlink()
        self.inquiry.with_user(self.sales_manager).unlink()

    def test_04_employee_cannot_read_inquiries(self):
        """Inquiries hold personal data, kept from the other employees."""
        with self.assertRaises(AccessError):
            self.inquiry.with_user(self.employee).read(['email'])

    def test_05_inquiries_of_other_companies(self):
        """An inquiry is only visible in its own company."""
        other = self.env['res.company'].create({'name': 'Other Mills'})
        inquiry = self.env['website.inquiry'].create({
            'inquirer': 'John Doe', 'email': 'john@example.com',
            'company_id': other.id})
        with self.assertRaises(AccessError):
            inquiry.with_user(self.salesman).read(['email'])
        self.assertIn(self.inquiry, self.env['website.inquiry'].with_user(
            self.salesman).search([]))

    def test_06_menus_follow_the_access(self):
        """Users only see the menus of the documents they can open."""
        self.assertNotIn('Textile Management', self._menus(self.employee))
        salesman = self._menus(self.salesman)
        self.assertIn('Sale Orders', salesman)
        self.assertIn('Website Inquiry', salesman)
        self.assertIn('Customer/Vendor Report', salesman)
        self.assertNotIn('Purchase Orders', salesman)
        self.assertNotIn('Manufacturing Orders', salesman)
        buyer = self._menus(self.buyer)
        self.assertIn('Purchase Orders', buyer)
        self.assertIn('Customer/Vendor Report', buyer)
        self.assertNotIn('Sale Orders', buyer)
        self.assertNotIn('Website Inquiry', buyer)

    def test_07_copy_keeps_the_textile_flag(self):
        """A copy stays textile wherever it is duplicated from, but not the
        feedback of the customer."""
        self.sale_order.write({'rating': '4', 'comment': 'Lovely'})
        copy = self.sale_order.copy()
        self.assertTrue(copy.is_textile_sale_order)
        self.assertFalse(copy.rating)
        self.assertFalse(copy.comment)
        self.assertTrue(self.purchase_order.copy().is_textile_purchase_order)
        product = self.env['product.product'].create(
            {'name': 'Cotton Shirt', 'is_textile_product': True})
        self.assertTrue(product.product_tmpl_id.copy().is_textile_product)
        component = self.env['product.product'].create({'name': 'Cotton'})
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'is_textile_bill_of_material': True,
            'bom_line_ids': [Command.create({'product_id': component.id})],
        })
        self.assertTrue(bom.copy().is_textile_bill_of_material)

    def test_08_rating_labels_match_the_stars(self):
        """The backend shows the rating with the words of the checkout."""
        labels = dict(self.env['sale.order']._fields['rating'].selection)
        self.assertEqual(
            [labels[value] for value in '1234'],
            ['Poor', 'Average', 'Nice', 'Excellent'])
