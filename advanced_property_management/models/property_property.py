# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _


class Property(models.Model):
    """A class for the model property to represent the property"""

    _name = "property.property"
    _description = "Property"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        string="Name", required=True, copy=False, help="Name of the Property"
    )
    code = fields.Char(
        string="Reference",
        readonly=True,
        copy=False,
        default=lambda self: _("New"),
        help="Sequence/code for the property",
    )
    property_type = fields.Selection(
        [
            ("land", "Land"),
            ("residential", "Residential"),
            ("commercial", "Commercial"),
            ("industry", "Industry"),
        ],
        string="Type",
        required=True,
        help="The type of the property",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("available", "Available"),
            ("rented", "Rented"),
            ("sold", "Sold"),
        ],
        required=True,
        string="Status",
        default="draft",
        help="* The 'Draft' status is used when the property is in draft.\n"
        "* The 'Available' status is used when the property is "
        "available or confirmed\n"
        "* The 'Rented' status is used when the property is rented.\n"
        "* The 'sold' status is used when the property is sold.\n",
    )
    street = fields.Char(string="Street", required=True, help="The street name")
    street2 = fields.Char(string="Street2", help="The street2 name")
    zip = fields.Char(string="Zip", change_default=True, help="Zip code for the place")
    city = fields.Char(string="City", help="The name of the city")
    country_id = fields.Many2one(
        "res.country",
        string="Country",
        ondelete="restrict",
        required=True,
        help="The name of the country",
    )
    state_id = fields.Many2one(
        "res.country.state",
        string="State",
        ondelete="restrict",
        tracking=True,
        domain="[('country_id', '=?', country_id)]",
        help="The name of the state",
    )
    latitude = fields.Float(
        string="Latitude",
        digits=(16, 5),
        help="The latitude of where the property is " "situated",
    )
    longitude = fields.Float(
        string="Longitude",
        digits=(16, 5),
        help="The longitude of where the property is " "situated",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Property Management Company",
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        "res.currency", string="Currency", related="company_id.currency_id"
    )
    image = fields.Binary(string="Image", help="Image of the property")
    construct_year = fields.Char(
        string="Construct Year", size=4, help="Year of construction of the property"
    )
    license_no = fields.Char(
        string="License No.", help="License number of the property"
    )
    landlord_id = fields.Many2one(
        "res.partner", string="LandLord", help="The owner of the property"
    )
    description = fields.Text(
        string="Description", help="A brief description about the property"
    )
    responsible_id = fields.Many2one(
        "res.users",
        string="Responsible Person",
        help="The responsible person for " "this property",
        default=lambda self: self.env.user,
    )
    type_residence = fields.Char(
        string="Type of Residence", help="The type of the residence"
    )
    total_floor = fields.Integer(
        string="Total Floor",
        default=1,
        help="The total number of floor in " "the property",
    )
    bedroom = fields.Integer(
        string="Bedrooms", help="Number of bedrooms in the property"
    )
    bathroom = fields.Integer(
        string="Bathrooms", help="Number of bathrooms in the property"
    )
    parking = fields.Integer(
        string="Parking",
        help="Number of cars or bikes that can be parked " "in the property",
    )
    furnishing = fields.Selection(
        [
            ("no_furnished", "Not Furnished"),
            ("half_furnished", "Partially Furnished"),
            ("furnished", "Fully Furnished"),
        ],
        string="Furnishing",
        help="Whether the residence is fully furnished or partially/half "
        "furnished or not at all furnished",
    )
    land_name = fields.Char(string="Land Name", help="The name of the land")
    land_area = fields.Char(
        string="Area In Hector", help="The area of the land in hector"
    )
    shop_name = fields.Char(string="Shop Name", help="The name of the shop")
    industry_name = fields.Char(string="Industry Name", help="The name of the industry")
    usage = fields.Char(
        string="Used For", help="For what purpose is this property used for"
    )
    location = fields.Char(string="Location", help="The location of the property")
    property_image_ids = fields.One2many(
        "property.image", "property_id", string="Property Images"
    )
    area_measurement_ids = fields.One2many(
        "property.area.measure", "property_id", string="Area Measurement"
    )
    total_sq_feet = fields.Float(
        string="Total Square Feet",
        compute="_compute_total_sq_feet",
        help="The total area square feet of the " "property",
    )
    facility_ids = fields.Many2many(
        "property.facility", string="Facilities", help="Facilities of the property"
    )
    nearby_connectivity_ids = fields.One2many(
        "property.nearby.connectivity", "property_id", string="Nearby Connectives"
    )
    property_tags = fields.Many2many(
        "property.tag", string="Property Tags", help="Tags for the property"
    )
    attachment_id = fields.Many2one("ir.attachment", string="Attachment")
    sale_rent = fields.Selection(
        [
            ("for_sale", "For Sale"),
            ("for_tenancy", "For Tenancy"),
            ("for_auction", "For Auction"),
        ],
        string="Sale | Rent",
        required=True,
    )
    unit_price = fields.Monetary(
        string="Sales Price", help="Selling price of the Property."
    )
    sale_id = fields.Many2one(
        "property.sale",
        string="Sale Order",
        help="The corresponding property sale",
        tracking=True,
    )
    rent_month = fields.Monetary(
        string="Rent/Month", help="Rent price per month", tracking=True
    )

    @api.model
    def create(self, vals):
        """Generating sequence number at the time of creation of record"""
        if vals.get("code", "New") == "New":
            vals["code"] = (
                self.env["ir.sequence"].next_by_code("property.property") or "New"
            )
        res = super(Property, self).create(vals)
        return res

    def _compute_total_sq_feet(self):
        """Calculates the total square feet of the property"""
        for rec in self:
            rec.total_sq_feet = sum(rec.mapped("area_measurement_ids").mapped("area"))

    @api.model
    def _geo_localize(self, street="", zip="", city="", state="", country=""):
        """Generate Latitude and Longitude based on address"""
        geo_obj = self.env["base.geocoder"]
        search = geo_obj.geo_query_address(
            street=street, zip=zip, city=city, state=state, country=country
        )
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(city=city, state=state, country=country)
            result = geo_obj.geo_find(search, force_country=country)
        return result

    @api.onchange("street", "zip", "city", "state_id", "country_id")
    def _onchange_address(self):
        """Writing Latitude and Longitude to the record"""
        for rec in self.with_context(lang="en_US"):
            result = rec._geo_localize(
                rec.street, rec.zip, rec.city, rec.state_id.name, rec.country_id.name
            )
            if result:
                rec.write(
                    {
                        "latitude": result[0],
                        "longitude": result[1],
                    }
                )

    def action_get_map(self):
        """Redirects to google map to show location based on latitude
        and longitude"""
        return {
            "type": "ir.actions.act_url",
            "name": "View Map",
            "target": "self",
            "url": "/map/%s/%s" % (self.latitude, self.longitude),
        }

    def action_available(self):
        """Set the state to available"""
        self.state = "available"

    def action_property_sale_view(self):
        """View Sale order Of the Property"""
        return {
            "name": "Property Sale: " + self.code,
            "view_mode": "tree,form",
            "res_model": "property.sale",
            "type": "ir.actions.act_window",
            "res_id": self.sale_id.id,
        }

    def action_property_rental_view(self):
        """View rental order Of the Property"""
        return {
            "name": "Property Rental: " + self.code,
            "view_mode": "tree,form",
            "res_model": "property.rental",
            "type": "ir.actions.act_window",
            "domain": [("property_id", "=", self.id)],
        }
