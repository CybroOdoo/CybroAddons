# -*- coding: utf-8 -*-
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    """
    Transient model for managing Oil ERP configuration settings.
    Inherits from 'res.config.settings' to provide a centralized interface
    for enabling/disabling Oil ERP modules and integrations.
    """
    _inherit = 'res.config.settings'

    module_oil_erp_lease = fields.Boolean("Upstream Lease Management",
                                          help="Enable this when module oil "
                                               "erp lease applies.")
    module_oil_erp_reservoir = fields.Boolean("Reservoir Management",
                                              help="Enable this when module oil "
                                                   "erp reservoir applies.")
    module_oil_erp_project = fields.Boolean("Upstream Projects & Tasks",
                                            help="Enable this when module oil "
                                                 "erp project applies.")
    module_oil_erp_equipment = fields.Boolean("Equipment Management",
                                              help="Enable this when module "
                                                   "oil erp equipment applies.")
    module_oil_erp_royalty = fields.Boolean("Royalty Management",
                                            help="Enable this when module "
                                                 "oil erp royalty applies.")
    module_oil_erp_hse = fields.Boolean("Health Safety, Checklist",
                                        help="Enable this when module oil "
                                             "erp hse applies.")
    module_oil_erp_employee = fields.Boolean("Employee Management",
                                             help="Enable this when module oil "
                                                  "erp employee applies.")
    module_oil_erp_transfers = fields.Boolean("Transfers",
                                              help="Enable this when module oil "
                                                   "erp transfers applies.")
    module_oil_erp_pipeline = fields.Boolean("Pipeline Management",
                                             help="Enable this when module oil "
                                                  "erp pipeline applies.")
    module_oil_erp_gate_pass = fields.Boolean("Gate Pass System",
                                              help="Enable this when module oil"
                                                   " erp gate pass applies.")
    module_oil_erp_manufacturing = fields.Boolean("Downstream Manufacturing",
                                                  help="Enable this when module"
                                                       " oil erp manufacturing applies.")
    module_oil_erp_inspection = fields.Boolean("Inspection & Checklist",
                                               help="Enable this when module oil"
                                                    " erp inspection applies.")
    enable_live_oil_api = fields.Boolean("Enable Real-Time Energy Benchmarks",
                                         compute="_compute_live_oil_settings",
                                         inverse="_inverse_enable_live_oil_api",
                                         help="Enable real-time crude oil and natural gas benchmarks.")
    live_oil_api_key = fields.Char("Market API Key (Optional)",
                                   compute="_compute_live_oil_settings",
                                   inverse="_inverse_live_oil_api_key",
                                   help="Optional API key for external real-time data providers.")
    enable_news_api = fields.Boolean("Enable News Integration",
                                     compute="_compute_news_settings",
                                     inverse="_inverse_enable_news_api",
                                     help="Enable live news api integration.")
    news_api_key = fields.Char("GNews API Key",
                               compute="_compute_news_settings",
                               inverse="_inverse_news_api_key",
                               help="Enter the GNews api key.")
    news_search_query = fields.Char("News Search Query",
                                    compute="_compute_news_settings",
                                    inverse="_inverse_news_search_query",
                                    help="Keywords used to fetch live news articles.")
    news_article_limit = fields.Integer("News Article Limit",
                                        compute="_compute_news_settings",
                                        inverse="_inverse_news_article_limit",
                                        default=8,
                                        help="Maximum number of live news articles to fetch.")
    # Compatibility aliases for stale settings views that still point to the
    # earlier OCN naming.
    enable_ocn = fields.Boolean("Enable OCN Integration",
                                compute="_compute_news_settings",
                                inverse="_inverse_enable_ocn",
                                help="Backward-compatible alias for news integration.")
    ocn_api_key = fields.Char("OCN API Key",
                              compute="_compute_news_settings",
                              inverse="_inverse_ocn_api_key",
                              help="Backward-compatible alias for the news API key.")
    ocn_search_query = fields.Char("OCN Search Query",
                                   compute="_compute_news_settings",
                                   inverse="_inverse_ocn_search_query",
                                   help="Backward-compatible alias for the news search query.")
    ocn_article_limit = fields.Integer("OCN Article Limit",
                                       compute="_compute_news_settings",
                                       inverse="_inverse_ocn_article_limit",
                                       default=8,
                                       help="Backward-compatible alias for the news article limit.")

    def _sanitize_article_limit(self, value):
        return min(max(int(value or 1), 1), 10)

    @api.depends_context('uid')
    def _compute_live_oil_settings(self):
        """Load live oil market integration values from ir.config_parameter."""
        config = self.env['ir.config_parameter'].sudo()
        enabled = config.get_param('oil_erp_base.enable_live_oil_api') == 'True'
        api_key = config.get_param('oil_erp_base.live_oil_api_key', '')
        for record in self:
            record.enable_live_oil_api = enabled
            record.live_oil_api_key = api_key

    @api.depends_context('uid')
    def _compute_news_settings(self):
        """Load news integration values from ir.config_parameter."""
        config = self.env['ir.config_parameter'].sudo()
        enabled = config.get_param('oil_erp_base.enable_news_api') == 'True'
        api_key = config.get_param('oil_erp_base.news_api_key', '')
        search_query = config.get_param('oil_erp_base.news_search_query', '')
        article_limit = self._sanitize_article_limit(
            config.get_param('oil_erp_base.news_article_limit', '8')
        )
        for record in self:
            record.enable_news_api = enabled
            record.news_api_key = api_key
            record.news_search_query = search_query
            record.news_article_limit = article_limit
            record.enable_ocn = enabled
            record.ocn_api_key = api_key
            record.ocn_search_query = search_query
            record.ocn_article_limit = article_limit

    def _set_news_param(self, key, value):
        self.env['ir.config_parameter'].sudo().set_param(key, value)

    def _set_live_oil_param(self, key, value):
        self.env['ir.config_parameter'].sudo().set_param(key, value)

    def _inverse_enable_live_oil_api(self):
        for record in self:
            record._set_live_oil_param(
                'oil_erp_base.enable_live_oil_api',
                bool(record.enable_live_oil_api)
            )

    def _inverse_live_oil_api_key(self):
        for record in self:
            record._set_live_oil_param(
                'oil_erp_base.live_oil_api_key',
                record.live_oil_api_key or ''
            )

    def _inverse_enable_news_api(self):
        for record in self:
            record._set_news_param('oil_erp_base.enable_news_api', bool(record.enable_news_api))

    def _inverse_news_api_key(self):
        for record in self:
            record._set_news_param('oil_erp_base.news_api_key', record.news_api_key or '')

    def _inverse_news_search_query(self):
        for record in self:
            record._set_news_param('oil_erp_base.news_search_query', record.news_search_query or '')

    def _inverse_news_article_limit(self):
        for record in self:
            limit = record._sanitize_article_limit(record.news_article_limit)
            record.news_article_limit = limit
            record._set_news_param('oil_erp_base.news_article_limit', limit)

    def _inverse_enable_ocn(self):
        for record in self:
            record._set_news_param('oil_erp_base.enable_news_api', bool(record.enable_ocn))

    def _inverse_ocn_api_key(self):
        for record in self:
            record._set_news_param('oil_erp_base.news_api_key', record.ocn_api_key or '')

    def _inverse_ocn_search_query(self):
        for record in self:
            record._set_news_param('oil_erp_base.news_search_query', record.ocn_search_query or '')

    def _inverse_ocn_article_limit(self):
        for record in self:
            limit = record._sanitize_article_limit(record.ocn_article_limit)
            record.ocn_article_limit = limit
            record._set_news_param('oil_erp_base.news_article_limit', limit)

    def set_values(self):
        """
        Extend set_values to clear stored integration keys when the
        corresponding integration is disabled.
        """
        super(ResConfigSettings, self).set_values()
        if not self.enable_live_oil_api:
            self.env['ir.config_parameter'].sudo().set_param(
                'oil_erp_base.live_oil_api_key', '')
        if not self.enable_news_api:
            self.env['ir.config_parameter'].sudo().set_param(
                'oil_erp_base.news_api_key', '')
            self.env['ir.config_parameter'].sudo().set_param(
                'oil_erp_base.news_search_query', '')

    @api.onchange('enable_live_oil_api')
    def _onchange_enable_live_oil_api(self):
        """
        Onchange handler to clear the live oil API key field in the UI when
        the integration toggle is turned off.
        """
        if not self.enable_live_oil_api:
            self.live_oil_api_key = ''

    @api.onchange('enable_news_api')
    def _onchange_enable_news_api(self):
        """
        Onchange handler to clear the news API key field in the UI when
        the integration toggle is turned off.
        """
        if not self.enable_news_api:
            self.news_api_key = ''
            self.news_search_query = ''
            self.ocn_api_key = ''
            self.ocn_search_query = ''

    @api.onchange('enable_ocn')
    def _onchange_enable_ocn(self):
        """
        Backward-compatible onchange for stale settings views using OCN fields.
        """
        if not self.enable_ocn:
            self.ocn_api_key = ''
            self.ocn_search_query = ''

    @api.onchange('news_article_limit')
    def _onchange_news_article_limit(self):
        self.news_article_limit = self._sanitize_article_limit(self.news_article_limit)

    @api.onchange('ocn_article_limit')
    def _onchange_ocn_article_limit(self):
        self.ocn_article_limit = self._sanitize_article_limit(self.ocn_article_limit)
