# -*- coding: utf-8 -*-
#############################################################################
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
###########################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models


class WorkersDetails(models.Model):
    """
    Workers Details

    This model manages workers involved in labour supply contracts.
    It stores worker personal details, skills, availability status,
    wage and billing rates, and links each worker to a related partner.
    It also provides multiple helper methods used for dashboard analytics.
    """

    _name = "workers.details"
    _description = "Workers"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Worker Name",
        required=True,
        help="Full name of the worker."
    )

    skill_ids = fields.Many2many(
        'skill.details',
        string="Skills",
        help="Skills or specializations possessed by the worker."
    )

    related_partner_id = fields.Many2one(
        'res.partner',
        string="Related Partner",
        readonly=True,
        help="Partner record automatically created and linked "
             "to this worker."
    )

    wage = fields.Monetary(
        string="Wage Per Day",
        help="Daily wage paid to the worker."
    )

    rate = fields.Monetary(
        string="Rate Per Day",
        help="Daily billing rate charged for the worker."
    )

    phone_number = fields.Char(
        string="Phone Number",
        help="Contact phone number of the worker."
    )

    email = fields.Char(
        string="Email",
        help="Email address of the worker."
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        help="Currency used for wage and rate calculation."
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        help="Company to which this worker belongs."
    )

    image_worker = fields.Binary(
        string="Worker Image",
        help="Profile image of the worker."
    )

    state = fields.Selection(
        [
            ('available', 'Available'),
            ('not_available', 'Not Available')
        ],
        string="Availability Status",
        default="available",
        help="Indicates whether the worker is currently available "
             "for assignment."
    )

    # ---------------------------------------------------------------------
    # ORM METHODS
    # ---------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals):
        """
        Create Worker Record

        Automatically creates a related partner record using
        the worker's basic contact details and links it to
        the worker record.
        """
        partner = self.env['res.partner'].create({
            'name': vals[0].get('name'),
            'phone': vals[0].get('phone_number'),
            'email': vals[0].get('email'),
            'image_1920': vals[0].get('image_worker'),
        })
        vals[0]['related_partner_id'] = partner.id
        return super().create(vals)

    # ---------------------------------------------------------------------
    # DASHBOARD DATA METHODS
    # ---------------------------------------------------------------------

    @api.model
    def get_labour_supply_details(self):
        """
        Get Ongoing Contract Count

        Returns the number of labour supply contracts that
        are currently active and invoiced.
        """
        count = self.env['labour.supply'].search_count([
            ('from_date', '<=', fields.Date.today()),
            ('to_date', '>=', fields.Date.today()),
            ('state', '=', 'invoiced'),
            ('company_id', '=', self.env.company.id)
        ])
        return {'ongoing_contract': count}

    @api.model
    def get_workers_count(self):
        """
        Get Workers Availability Count

        Returns the count of available and unavailable workers
        for dashboard visualization.
        """
        workers = self.search([('company_id', '=', self.env.company.id)])

        return {
            'state': ['Not Available', 'Available'],
            'count': [
                len(workers.filtered(lambda w: w.state == 'not_available')),
                len(workers.filtered(lambda w: w.state == 'available')),
            ],
        }

    @api.model
    def get_top_customer(self):
        """
        Get Top Customers

        Returns the top ten customers based on the number
        of labour supply contracts.
        """
        query = """
            SELECT rp.id, rp.name, rp.email,
                   COUNT(ls.company_id) AS count
            FROM labour_supply ls
            INNER JOIN res_partner rp
                ON rp.id = ls.customer_id
            WHERE ls.company_id = %s
            GROUP BY rp.id
            ORDER BY count DESC
            LIMIT 10
        """
        self.env.cr.execute(query, (self.env.company.id,))
        return {'customer': self.env.cr.dictfetchall()}

    @api.model
    def get_skills_available(self):
        """
        Get Available Skills

        Returns a list of skills available under the
        current company for dashboard display.
        """
        query = """
            SELECT name, company_id
            FROM skill_details
            WHERE company_id = %s
            LIMIT 10
        """
        self.env.cr.execute(query, (self.env.company.id,))
        return {'skill': self.env.cr.dictfetchall()}

    @api.model
    def get_workers_available(self):
        """
        Get Available Workers

        Returns a list of currently available workers
        for dashboard display.
        """
        query = """
            SELECT *
            FROM workers_details
            WHERE state = 'available'
              AND company_id = %s
            LIMIT 10
        """
        self.env.cr.execute(query, (self.env.company.id,))
        return {'workers': self.env.cr.dictfetchall()}

    @api.model
    def get_total_invoiced_amount(self):
        """
        Get Total Invoiced Amount

        Returns the total invoiced amount from all
        invoiced labour supply contracts.
        """
        contracts = self.env['labour.supply'].search([
            ('state', '=', 'invoiced'),
            ('company_id', '=', self.env.company.id)
        ])
        return {'invoiced_amount': sum(contracts.mapped('total_amount'))}

    @api.model
    def get_expected_amount(self):
        """
        Get Expected Revenue

        Returns the expected revenue from active labour
        supply contracts that are not expired or draft.
        """
        contracts = self.env['labour.supply'].search([
            ('state', 'not in', ['ready', 'expired', 'draft']),
            ('company_id', '=', self.env.company.id)
        ])
        return {'expected_amount': sum(contracts.mapped('total_amount'))}

    @api.model
    def get_contract_count_state(self):
        """
        Get Contract Count by State

        Returns the number of labour supply contracts
        grouped by their current state.
        """
        labour_supply = self.env['labour.supply'].search([
            ('company_id', '=', self.env.company.id)
        ])

        states = ['draft', 'ready', 'confirmed', 'invoiced', 'expired', 'canceled']
        labels = ['Draft', 'Ready', 'Confirmed', 'Invoiced', 'Expired', 'Canceled']

        return {
            'state': labels,
            'count': [len(labour_supply.filtered(lambda r: r.state == s))
                      for s in states]
        }

    @api.model
    def get_contract_amount(self):
        """
        Get Recent Contract Amounts

        Returns the latest labour supply contract references
        and their corresponding amounts.
        """
        contracts = self.env['labour.supply'].search(
            [('company_id', '=', self.env.company.id)], limit=5
        )

        return {
            'sequence': contracts.mapped('sequence_number'),
            'amount': contracts.mapped('total_amount'),
        }

    @api.model
    def get_details_amount(self, option):
        """
        Get Contract Amounts by Period

        Returns contract amounts filtered by daily,
        monthly, or yearly period.

        :param option: Filter option ('daily', 'monthly', 'yearly')
        """
        today = fields.Date.today()
        first_day = today + relativedelta(day=1)
        last_day = today + relativedelta(day=31)
        first_month = first_day + relativedelta(month=1)
        last_month = last_day + relativedelta(month=12)

        contracts = self.env['labour.supply'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=5)

        if option == 'daily':
            contracts = contracts.filtered(lambda r: r.from_date == today)
        elif option == 'monthly':
            contracts = contracts.filtered(
                lambda r: r.from_date and first_day <= r.from_date <= last_day)
        elif option == 'yearly':
            contracts = contracts.filtered(
                lambda r: r.from_date and first_month <= r.from_date <= last_month)

        return {
            'sequence': contracts.mapped('sequence_number'),
            'amount': contracts.mapped('total_amount'),
        }

    @api.model
    def get_contract_count_customer(self):
        """
        Get Contract Count per Customer

        Returns the number of labour supply contracts
        grouped by customer.
        """
        labour_supply = self.env['labour.supply'].search([
            ('company_id', '=', self.env.company.id)
        ])

        customer_map = {}
        for contract in labour_supply:
            customer = contract.customer_id.name
            customer_map[customer] = customer_map.get(customer, 0) + 1

        return {
            'name': list(customer_map.keys()),
            'count': list(customer_map.values()),
        }

