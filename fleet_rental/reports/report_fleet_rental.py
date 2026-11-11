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
from odoo import fields, models, tools


class FleetRentalReport(models.Model):
    _name = "report.fleet.rental"
    _description = "Fleet Rental Analysis"
    _order = 'name desc'
    _auto = False

    name = fields.Char(help="Report name")
    customer_id = fields.Many2one(comodel_name='res.partner', help="Customer")
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', help="Vehicle")
    car_brand = fields.Char(help="Manufacture of the fleet")
    car_color = fields.Char(help="color of the fleet")
    cost = fields.Float(string="Rent Cost", help="Rental cost")
    rent_start_date = fields.Date(help="Contract start date")
    rent_end_date = fields.Date(help="Contract end date")
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'), ('reserved', 'Reserved'), ('running', 'Running'),
            ('cancel', 'Cancel'), ('checking', 'Checking'), ('invoice', 'Invoice'), ('done', 'Done'),
        ],
        help="State of the contract",
    )
    cost_frequency = fields.Selection(
        selection=[('no', 'No'), ('daily', 'Daily'), ('weekly', 'Weekly'),
                   ('monthly', 'Monthly'),
                   ('yearly', 'Yearly')],
        string="Recurring Cost Frequency",
        help="Cost frequency",
    )
    total = fields.Float(string="Total(Tools)", help="Total amount")
    tools_missing_cost = fields.Float(string="Tools missing cost", help="Missing tools cost")
    damage_cost = fields.Float(string="Damage cost", help="Damage cost")
    damage_cost_sub = fields.Float(string="Damage Sub Cost", help="Damage sub cost")
    total_cost = fields.Float(string="Total cost", help="Total cost of the contract")

    def _select(self):
        """
            Construct a SQL select query string with specific fields.
        """
        return """
             SELECT
                    (select 1 ) AS nbr,
                    t.id as id,
                    t.name as name,
                    t.car_brand as car_brand,
                    t.customer_id as customer_id,
                    t.vehicle_id as vehicle_id,
                    t.car_color as car_color,
                    t.cost as cost,
                    t.rent_start_date as rent_start_date,
                    t.rent_end_date as rent_end_date,
                    t.state as state,
                    t.cost_frequency as cost_frequency,
                    t.total as total,
                    t.tools_missing_cost as tools_missing_cost,
                    t.damage_cost as damage_cost,
                    t.damage_cost_sub as damage_cost_sub,
                    t.total_cost as total_cost
        """

    def _group_by(self):
        """
            Construct a SQL GROUP BY query string with specific fields.
        """
        return """
                GROUP BY
                    t.id,
                    name,
                    car_brand,
                    customer_id,
                    vehicle_id,
                    car_color,
                    cost,
                    rent_start_date,
                    rent_end_date,
                    state,
                    cost_frequency,
                    total,
                    tools_missing_cost,
                    damage_cost,
                    damage_cost_sub,
                    total_cost
        """

    def init(self):
        """
            Initialize the module and create a database view for reporting
            fleet rentals.
            Drop the existing 'report_fleet_rental' view if it already exists.
            Create a new view with the SQL select and group by queries.
        """
        tools.sql.drop_view_if_exists(self.env.cr, 'report_fleet_rental')
        self.env.cr.execute("""
            CREATE view report_fleet_rental as
              %s
              FROM car_rental_contract t
                %s
        """ % (self._select(), self._group_by()))
