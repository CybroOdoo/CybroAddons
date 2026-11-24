################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.theme_buildcraft import _theme_buildcraft_uninstall_hook

THEME_URLS = ['/about', '/services', '/projects', '/team']
CSRF_ANCHOR = '<input type="hidden" name="csrf_token" value="'


@tagged('post_install', '-at_install')
class TestThemeBuildcraft(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env['website'].get_current_website()
        cls.theme = cls.env['ir.module.module'].search(
            [('name', '=', 'theme_buildcraft')])
        cls.theme._theme_load(cls.website)
        Project = cls.env['buildcraft.project']
        cls.tower = Project.create({
            'name': 'Marina Tower', 'category': 'commercial',
            'location': 'Dubai, UAE', 'client': 'Gulf Holdings',
            'value': 'AED 380M', 'year': '2024'})
        cls.mall = Project.create({
            'name': 'Harbour Mall', 'category': 'commercial'})
        cls.villa = Project.create({
            'name': 'Palm Villa', 'category': 'residential'})
        cls.bridge = Project.create({
            'name': 'Creek Bridge', 'category': 'infrastructure'})
        cls.draft = Project.create({
            'name': 'Secret Draft', 'category': 'commercial',
            'is_published': False})
        blog = cls.env['blog.blog'].create({'name': 'Site News'})
        cls.post = cls.env['blog.post'].create({
            'name': 'Steel Prices Rise', 'blog_id': blog.id,
            'author_id': cls.env.ref('base.partner_admin').id,
            'is_published': True})

    def _csrf(self, url):
        page = self.url_open(url).text
        return page.partition(CSRF_ANCHOR)[2].partition('"')[0]

    def test_01_theme_pages_and_menus(self):
        """Loading the theme adds its pages and menus to the website"""
        pages = self.env['website.page'].search([
            ('url', 'in', THEME_URLS), ('website_id', '=', self.website.id)])
        self.assertEqual(sorted(pages.mapped('url')), sorted(THEME_URLS))
        menus = self.website.menu_id.child_id
        for name in ('About', 'Services', 'Projects', 'Team'):
            self.assertIn(name, menus.mapped('name'))

    def test_02_pages_render(self):
        """Every page of the theme opens with the theme header and footer"""
        for url in ['/', '/blog', '/contactus'] + THEME_URLS:
            response = self.url_open(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertIn('logo_buildcraft.png', response.text, url)
            self.assertIn('id="mobile-menu"', response.text, url)

    def test_02b_blog_page(self):
        """Visitors see the posts of the blog with their author"""
        page = self.url_open('/blog').text
        self.assertIn('Steel Prices Rise', page)
        self.assertIn(self.post.author_name, page)

    def test_03_projects_page(self):
        """The Projects page shows the published projects only"""
        page = self.url_open('/projects').text
        for project in self.tower | self.villa | self.bridge:
            self.assertIn(project.name, page)
        self.assertNotIn('Secret Draft', page)

    def test_04_project_detail(self):
        """The page of a project shows its details and related projects,
        those of the same category first"""
        response = self.url_open(f'/project/{self.tower.id}')
        self.assertEqual(response.status_code, 200)
        page = response.text
        for text in ('Marina Tower', 'Dubai, UAE', 'Gulf Holdings', 'AED 380M'):
            self.assertIn(text, page)
        self.assertIn(f'/project/{self.mall.id}', page)
        self.assertNotIn(f'/project/{self.draft.id}"', page)
        # Fewer than 3 projects of the category: others fill the list
        related = page.count('/project/')
        self.assertGreaterEqual(related, 3)

    def test_05_project_detail_not_found(self):
        """Unpublished and missing projects are not found"""
        self.assertEqual(
            self.url_open(f'/project/{self.draft.id}').status_code, 404)
        self.assertEqual(self.url_open('/project/999999999').status_code, 404)

    def test_06_access_rights(self):
        """Visitors and portal users see the published projects, employees
        read them, and the website designers manage them"""
        Project = self.env['buildcraft.project']
        public = self.env.ref('base.public_user')
        portal = new_test_user(self.env, login='bc_portal',
                               groups='base.group_portal')
        employee = new_test_user(self.env, login='bc_employee',
                                 groups='base.group_user')
        designer = new_test_user(
            self.env, login='bc_designer',
            groups='base.group_user,website.group_website_designer')
        for user in (public, portal):
            visible = Project.with_user(user).search([])
            self.assertIn(self.tower, visible)
            self.assertNotIn(self.draft, visible)
        self.assertIn(self.draft, Project.with_user(employee).search([]))
        with self.assertRaises(AccessError):
            Project.with_user(employee).create({'name': 'Not allowed'})
        with self.assertRaises(AccessError):
            self.tower.with_user(employee).write({'name': 'Not allowed'})
        project = Project.with_user(designer).create({
            'name': 'New Office', 'category': 'luxury'})
        project.write({'is_published': False})
        project.unlink()
        menu = self.env.ref('theme_buildcraft.menu_buildcraft_project_root')
        self.assertIn(menu.id, self.env['ir.ui.menu'].with_user(
            designer)._visible_menu_ids())
        self.assertNotIn(menu.id, self.env['ir.ui.menu'].with_user(
            employee)._visible_menu_ids())

    def test_07_header_sign_in_and_logout(self):
        """Visitors can sign in from the header and users can log out"""
        page = self.url_open('/').text
        self.assertIn('/web/login', page)
        new_test_user(self.env, login='bc_customer', name='Ruby Customer',
                      groups='base.group_portal')
        self.authenticate('bc_customer', 'bc_customer')
        page = self.url_open('/').text
        self.assertIn('/web/session/logout', page)
        self.assertIn('Ruby Customer', page)

    def test_08_newsletter_subscription(self):
        """The newsletter form of the blog page creates a lead"""
        page = self.url_open('/blog').text
        self.assertIn('bc-newsletter-form', page)
        response = self.url_open('/website/form/crm.lead', data={
            'name': 'Newsletter Subscription',
            'email_from': 'reader@example.com',
            'csrf_token': self._csrf('/blog'),
        })
        self.assertEqual(response.status_code, 200)
        lead = self.env['crm.lead'].search(
            [('email_from', '=', 'reader@example.com')])
        self.assertEqual(lead.name, 'Newsletter Subscription')

    def test_09_contact_form(self):
        """The contact form creates a lead with the visitor's details"""
        response = self.url_open('/website/form/crm.lead', data={
            'name': 'Website Contact Request',
            'contact_name': 'John',
            'email_from': 'john@example.com',
            'phone': '+971500000000',
            'description': 'A new warehouse',
            'csrf_token': self._csrf('/contactus'),
        })
        self.assertEqual(response.status_code, 200)
        lead = self.env['crm.lead'].search(
            [('email_from', '=', 'john@example.com')])
        self.assertEqual(lead.contact_name, 'John')

    def test_10_uninstall_hook(self):
        """Uninstalling the theme removes its website menus"""
        _theme_buildcraft_uninstall_hook(self.env)
        names = self.env['website.menu'].search([
            ('url', 'in', THEME_URLS)]).mapped('name')
        for name in ('About', 'Services', 'Projects', 'Team'):
            self.assertNotIn(name, names)

    def test_11_tour(self):
        """Subscribe to the newsletter, filter the projects and use the
        mobile menu"""
        self.start_tour('/blog', 'theme_buildcraft_tour', login=None)
        self.assertTrue(self.env['crm.lead'].search(
            [('email_from', '=', 'tour.reader@example.com')]))
