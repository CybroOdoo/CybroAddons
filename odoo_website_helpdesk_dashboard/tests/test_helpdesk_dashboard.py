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
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged


class HelpdeskDashboardCommon(TransactionCase):
    """Tickets in each stage, priority and team of the dashboard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Ticket = cls.env['ticket.helpdesk']
        cls.Ticket.search([]).unlink()
        cls.env['team.helpdesk'].search([]).unlink()
        cls.manager = new_test_user(
            cls.env, login='hd_dashboard_manager',
            groups='base.group_user,odoo_website_helpdesk.helpdesk_manager')
        cls.support_team = cls.env['team.helpdesk'].create(
            {'name': 'Support Team'})
        cls.sales_team = cls.env['team.helpdesk'].create(
            {'name': 'Sales Team'})
        cls.customer = cls.env['res.partner'].create({'name': 'Anna Customer'})

        def stage(xml_id):
            return cls.env.ref(f'odoo_website_helpdesk.{xml_id}')

        values = [
            ('stage_inbox', '0', cls.support_team),
            ('stage_draft', '1', cls.support_team),
            ('stage_in_progress', '1', cls.support_team),
            ('stage_in_progress', '3', cls.sales_team),
            ('stage_done', '4', cls.env['team.helpdesk']),
        ]
        cls.tickets = cls.Ticket.create([{
            'subject': f'Ticket {index}',
            'description': 'Something does not work',
            'customer_id': cls.customer.id,
            'stage_id': stage(stage_xml_id).id,
            'priority': priority,
            'team_id': team.id,
            'assigned_user_id': cls.manager.id,
        } for index, (stage_xml_id, priority, team) in enumerate(values)])
        cls.tickets[-1].review = 'Great support'


@tagged('post_install', '-at_install')
class TestHelpdeskDashboard(HelpdeskDashboardCommon):

    def test_01_counters(self):
        """The cards count the new, in progress and done tickets and the
        helpdesk teams, and the review counter the reviewed tickets."""
        data = self.Ticket.with_user(self.manager).get_dashboard_data()
        self.assertEqual(data['counts'],
                         {'new': 2, 'in_progress': 2, 'done': 1})
        self.assertEqual(data['team_count'], 2)
        self.assertEqual(data['review_count'], 1)
        tickets = self.Ticket.search(
            [('stage_id', 'in', data['stage_ids']['new'])])
        self.assertEqual(tickets, self.tickets[:2],
                         "A card opens the tickets it counts")

    def test_02_priorities(self):
        """The priority bars show the share of the tickets of each priority,
        for every priority, in the order of the selection."""
        data = self.Ticket.with_user(self.manager).get_dashboard_data()
        self.assertEqual(
            [(item['key'], item['count'], item['percent'])
             for item in data['priorities']],
            [('0', 1, 20), ('1', 2, 40), ('2', 0, 0), ('3', 1, 20),
             ('4', 1, 20)])
        self.assertEqual(data['priorities'][4]['label'], 'Very High')

    def test_03_team_chart(self):
        """The team chart shows the tickets of each team, the busiest team
        first, without the tickets that have no team."""
        data = self.Ticket.with_user(self.manager).get_dashboard_data()
        self.assertEqual(data['team_chart'], {
            'labels': ['Support Team', 'Sales Team'], 'values': [3, 1]})

    def test_04_latest_tickets(self):
        """The latest tickets are listed newest first with their customer,
        assigned user, subject and priority label."""
        data = self.Ticket.with_user(self.manager).get_dashboard_data()
        self.assertEqual([ticket['id'] for ticket in data['tickets']],
                         self.tickets.ids[::-1])
        self.assertEqual(data['tickets'][0], {
            'id': self.tickets[-1].id,
            'name': self.tickets[-1].name,
            'customer': 'Anna Customer',
            'assigned_to': self.manager.name,
            'subject': 'Ticket 4',
            'priority': 'Very High',
        })

    def test_05_latest_tickets_limit(self):
        """Only the ten newest tickets are listed, while the counters still
        count every ticket."""
        self.Ticket.create([{
            'subject': f'Extra {index}', 'description': 'More',
            'customer_name': 'Website visitor',
            'stage_id': self.env.ref('odoo_website_helpdesk.stage_inbox').id,
        } for index in range(8)])
        data = self.Ticket.get_dashboard_data()
        self.assertEqual(len(data['tickets']), 10)
        self.assertEqual(data['counts']['new'], 10)
        self.assertEqual(data['tickets'][0]['customer'], 'Website visitor',
                         "Tickets from the website show the visitor name")
        self.assertEqual(data['tickets'][0]['assigned_to'], '')

    def test_06_empty_dashboard(self):
        """The dashboard works without any ticket or team."""
        self.tickets.unlink()
        self.env['team.helpdesk'].search([]).unlink()
        data = self.Ticket.get_dashboard_data()
        self.assertEqual(data['counts'],
                         {'new': 0, 'in_progress': 0, 'done': 0})
        self.assertEqual(data['tickets'], [])
        self.assertEqual(data['team_chart'], {'labels': [], 'values': []})
        self.assertTrue(all(item['percent'] == 0
                            for item in data['priorities']))

    def test_07_access(self):
        """A HelpDesk user gets the dashboard data, while an internal user
        without HelpDesk access gets an access error and no menu."""
        helpdesk_user = new_test_user(
            self.env, login='hd_dashboard_user',
            groups='base.group_user,odoo_website_helpdesk.helpdesk_user')
        data = self.Ticket.with_user(helpdesk_user).get_dashboard_data()
        self.assertEqual(data['counts'],
                         {'new': 2, 'in_progress': 2, 'done': 1})
        employee = new_test_user(self.env, login='hd_dashboard_employee',
                                 groups='base.group_user')
        self.assertFalse(employee.has_group(
            'odoo_website_helpdesk.helpdesk_user'))
        with self.assertRaises(AccessError):
            self.Ticket.with_user(employee).get_dashboard_data()
        menu = self.env.ref(
            'odoo_website_helpdesk_dashboard.menu_helpdesk_dashboard_new')
        visible = self.env['ir.ui.menu'].with_user(
            employee)._visible_menu_ids()
        self.assertNotIn(menu.id, visible)
        visible = self.env['ir.ui.menu'].with_user(
            helpdesk_user)._visible_menu_ids()
        self.assertIn(menu.id, visible)
        admin = new_test_user(self.env, login='hd_dashboard_admin',
                              groups='base.group_user,base.group_system')
        self.assertFalse(admin.has_group(
            'odoo_website_helpdesk.helpdesk_user'))
        visible = self.env['ir.ui.menu'].with_user(admin)._visible_menu_ids()
        self.assertIn(menu.id, visible)
        data = self.Ticket.with_user(admin).get_dashboard_data()
        self.assertEqual(data['counts']['new'], 2)

    def test_08_dashboard_menu(self):
        """The HelpDesk app opens on the dashboard, for HelpDesk users and
        administrators."""
        menu = self.env.ref(
            'odoo_website_helpdesk_dashboard.menu_helpdesk_dashboard_new')
        self.assertEqual(menu.parent_id,
                         self.env.ref('odoo_website_helpdesk.menu_helpdesk'))
        self.assertEqual(menu.action.tag, 'helpdesk_dashboard')
        self.assertEqual(
            menu.group_ids,
            self.env.ref('odoo_website_helpdesk.helpdesk_user')
            | self.env.ref('base.group_system'))
        children = menu.parent_id.child_id.sorted('sequence')
        self.assertEqual(children[0], menu)


@tagged('post_install', '-at_install')
class TestHelpdeskDashboardTour(HttpCase, HelpdeskDashboardCommon):

    def test_tour_helpdesk_dashboard(self):
        """A HelpDesk manager opens the dashboard from the HelpDesk app,
        checks the counters and charts, and opens tickets from it."""
        self.start_tour('/odoo', 'helpdesk_dashboard_tour',
                        login=self.manager.login)

    def test_tour_helpdesk_dashboard_admin(self):
        """The administrator, without any HelpDesk group, also gets the
        dashboard when opening the HelpDesk app."""
        self.start_tour('/odoo', 'helpdesk_dashboard_tour', login='admin')
