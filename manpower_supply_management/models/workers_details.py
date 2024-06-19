# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ranjith R(<https://www.cybrosys.com>)
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
        Class to create workers
        """
    _name = "workers.details"
    _description = "Workers"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", required=True, help="Field to type name")
    skill_ids = fields.Many2many('skill.details', string="Skills",
                                 help="Field to choose skills of worker")
    related_partner_id = fields.Many2one('res.partner',
                                         string="Related partner",
                                         readonly=True,
                                         help="Field represent the related "
                                              "partner")
    wage = fields.Monetary(string="Wage per day",
                           help="Field to give wage of worker")
    rate = fields.Monetary(string="Rate per day",
                           help="Field to give rate of worker")
    phone_number = fields.Char(string="Phone number",
                               help="Field to give address of worker")
    email = fields.Char(string=" Email", help="Field to give email of worker")
    currency_id = fields.Many2one('res.currency',
                                  string='Currency', help="Currency",
                                  related='company_id.currency_id')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True, help="Company",
                                 default=lambda self: self.env.company)
    image_worker = fields.Binary(string="Image",
                                 help="Field to give image of worker")
    state = fields.Selection(
        [('available', 'Available'),
         ('not_available', 'Not Available')], default="available",
        string="State", help="Field to specify state of worker")

    @api.model
    def create(self, vals):
        """ Function to created related partner"""
        partner = self.env['res.partner'].create({
            'name': vals['name'],
            'phone': vals['phone_number'],
            'email': vals['email'],
            'image_1920': vals['image_worker'],
        })
        vals['related_partner_id'] = partner.id
        self.related_partner_id = vals['related_partner_id']
        return super(WorkersDetails, self).create(vals)

    @api.model
    def get_labour_supply_details(self):
        """ Summary:
               function to get the number of ongoing contract for dashboard
            return:
               length of ongoing contract
              """
        labour_supply_ongoing = self.env['labour.supply'].search_count(
            [('from_date', '<=', fields.Date.today()),
             ('to_date', '>=', fields.Date.today()),
             ('state', '=', 'invoiced'),
             ('company_id', '=', self.env.company.id)])
        return {'ongoing_contract': labour_supply_ongoing}

    @api.model
    def get_workers_count(self):
        """ Summary:
                  function to get the number of workers for dashboard
            return:
             states and count of labour supply in that state
              """
        state = []
        count = []
        workers = self.env['workers.details'].search(
            [('company_id', '=', self.env.company.id)])
        not_available_labour = workers.filtered(
            lambda record: record.state == 'not_available')
        state.append("Not Available")
        count.append(len(not_available_labour))
        available_labour = workers.filtered(
            lambda record: record.state == 'available')
        state.append("Available")
        count.append(len(available_labour))
        values = {
            'state': state,
            'count': count,
        }
        return values

    @api.model
    def get_top_customer(self):
        """ Summary:
                function to top ten customer for dashboard
         return:
               return record of customers
                """
        query = (
            'select res_partner.id,res_partner.name,'
            'res_partner.email,count(labour_supply.company_id)\n'
            '                                    from labour_supply\n'
            '                                  inner join res_partner on '
            'res_partner.id=labour_supply.customer_id')
        query += f" where labour_supply.company_id = {self.env.company.id:d} "
        query += """group by res_partner.id order by count desc limit 10"""
        self.env.cr.execute(query)
        datas = self.env.cr.dictfetchall()
        return {'customer': datas}

    @api.model
    def get_skills_available(self):
        """ Summary:
                  function to  get skill available for dashboard
              return:
                  skills as data
                """

        query = """select name,company_id from skill_details"""
        query += f" where skill_details.company_id = {self.env.company.id:d} "
        query += """limit 10"""
        self.env.cr.execute(query)
        datas = self.env.cr.dictfetchall()
        return {'skill': datas}

    @api.model
    def get_workers_available(self):
        """ Summary:
                    function to get the number of workers for dashboard
              return:
               worker details
                """
        query = """select * from workers_details
         where state ='available'"""
        query += f" and workers_details.company_id = {self.env.company.id:d} "
        query += """limit 10"""
        self.env.cr.execute(query)
        datas = self.env.cr.dictfetchall()

        return {'workers': datas}

    @api.model
    def get_total_invoiced_amount(self):
        """
        Summary:
            function to get the number of  contract  on the
            basis of customer and state for dashboard
        return:
            total invoice amount
                     """
        labour_supply_ongoing = self.env['labour.supply'].search(
            [('state', '=', 'invoiced'),
             ('company_id', '=', self.env.user.company_id.id)])
        invoiced_amount = 0
        for contract in labour_supply_ongoing:
            invoiced_amount = invoiced_amount + contract.total_amount
        return {'invoiced_amount': invoiced_amount}

    @api.model
    def get_expected_amount(self):
        """
        Summary:
          function to get expecting amount
        return:
           total expecting amount
                               """
        labour_supply_ongoing = self.env['labour.supply'].search(
            [('state', 'not in', ['ready', 'expired', 'draft'])])
        expected_amount = 0
        for contract in labour_supply_ongoing:
            expected_amount = expected_amount + contract.total_amount
        return {'expected_amount': expected_amount}

    @api.model
    def get_contract_count_state(self):
        """Summary:function to get the number of  contract  on the basis of
           customer and state for dashboard initially
        return:
              count and state
                     """
        state = []
        count = []
        labour_supply = self.env['labour.supply'].search(
            [('company_id', '=', self.env.company.id)])
        labour_supply_draft = labour_supply.filtered(
            lambda record: record.state == 'draft')
        state.append("Draft")
        count.append(len(labour_supply_draft))
        labour_supply_ready = labour_supply.filtered(
            lambda record: record.state == 'ready')
        state.append("Ready")
        count.append(len(labour_supply_ready))
        labour_supply_confirm = labour_supply.filtered(
            lambda record: record.state == 'confirm')
        state.append("Confirm")
        count.append(len(labour_supply_confirm))
        labour_supply_invoiced = labour_supply.filtered(
            lambda record: record.state == 'invoiced')
        state.append("Invoiced")
        count.append(len(labour_supply_invoiced))
        labour_supply_expired = labour_supply.filtered(
            lambda record: record.state == 'expired')
        state.append("Expired")
        count.append(len(labour_supply_expired))
        labour_supply_cancelled = labour_supply.filtered(
            lambda record: record.state == 'cancelled')
        state.append("Cancelled")
        count.append(len(labour_supply_cancelled))
        values = {
            'state': state,
            'count': count,
        }
        return values

    @api.model
    def get_contract_amount(self):
        """
    Summary:
        function to get the amount of  contract  on the
    return:
           sequence and amount"""
        sequence = []
        amount = []
        labour_supply = self.env['labour.supply'].search(
            [('company_id', '=', self.env.company.id)], limit=5)
        for contract in labour_supply:
            sequence.append(contract.sequence_number)
            amount.append(contract.total_amount)
        values = {
            'sequence': sequence,
            'amount': amount,
        }
        return values

    @api.model
    def get_details_amount(self, option):
        """
        Summary:
            function to get the amount of  contract  on the basis of filter
              dashboard initially
        Args:
            option:filter value on dashboard
        returns:
             partner and amount
                     """
        sample_date = fields.Date.today()
        first_day = sample_date + relativedelta(day=1)
        last_day = sample_date + relativedelta(day=31)
        first_month = first_day + relativedelta(month=1)
        last_month = last_day + relativedelta(month=12)
        sequence = []
        amount = []
        labour_supply = self.env['labour.supply'].search(
            [('company_id', '=', self.env.company.id)], limit=5)

        if option == 'daily':
            labour_supply = labour_supply.filtered(
                lambda record: record.from_date == sample_date)
        elif option == "monthly":
            labour_supply = labour_supply.filtered(
                lambda record: first_day <= record.from_date <= last_day)
        elif option == "yearly":
            labour_supply = labour_supply.filtered(
                lambda record: first_month <= record.from_date <= last_month)

        for contract in labour_supply:
            sequence.append(contract.sequence_number)
            amount.append(contract.total_amount)

        values = {
            'sequence': sequence,
            'amount': amount,
        }
        return values

    @api.model
    def get_contract_count_customer(self):
        """
        Summary:
           function to get the number of  contract  on the basis of
           customer and state for dashboard initially
        returns:
            partner and count of contract
                     """
        labour_supply = self.env['labour.supply'].search(
            [('company_id', '=', self.env.company.id)])

        customer = []
        customer_id = []
        count = []
        for contract in labour_supply:
            if contract.customer_id.id not in customer_id:
                number = self.env['labour.supply'].search_count(
                    [('customer_id', '=', contract.customer_id.id),
                     ('company_id', '=', self.env.company.id)])
                customer.append(contract.customer_id.name)
                customer_id.append(contract.customer_id.id)
                count.append(number)
        values = {
            'name': customer,
            'count': count,
        }
        return values
