# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models

class AccountMove(models.Model):
    """ AccountMove tests """
    _inherit = 'account.move'

    def button_cancel(self):
        """ Override button_cancel to update car.workshop state """
        for move in self:
            if move.invoice_origin:
                workshops = self.env['car.workshop'].search([('name', '=', move.invoice_origin)])
                for workshop in workshops:
                    for line in move.invoice_line_ids:
                        if line.product_id:
                            materials = workshop.materials_ids.filtered(
                                lambda m: m.material_product_id == line.product_id and m.is_invoiced
                            )
                            if materials:
                                exact_match = materials.filtered(lambda m: m.quantity == line.quantity and
                                                                           m.price == line.price_unit)
                                if exact_match:
                                    exact_match[0].is_invoiced = False
                                else:
                                    materials[0].is_invoiced = False
                        elif line.name:
                            works = workshop.planned_work_ids.filtered(
                                lambda w: w.planned_work_id == line.name and w.is_invoiced
                            )
                            if works:
                                exact_match = works.filtered(lambda w: w.work_cost == line.price_unit)
                                if exact_match:
                                    exact_match[0].is_invoiced = False
                                else:
                                    works[0].is_invoiced = False
        return super(AccountMove, self).button_cancel()

    def unlink(self):
        """ Override unlink to update car.workshop state """
        for move in self:
            if move.invoice_origin:
                workshops = self.env['car.workshop'].search([('name', '=', move.invoice_origin)])
                for workshop in workshops:
                    for line in move.invoice_line_ids:
                        if line.product_id:
                            materials = workshop.materials_ids.filtered(
                                lambda m: m.material_product_id == line.product_id and m.is_invoiced
                            )
                            if materials:
                                exact_match = materials.filtered(lambda m: m.quantity == line.quantity and
                                                                           m.price == line.price_unit)
                                if exact_match:
                                    exact_match[0].is_invoiced = False
                                else:
                                    materials[0].is_invoiced = False
                        elif line.name:
                            works = workshop.planned_work_ids.filtered(
                                lambda w: w.planned_work_id == line.name and w.is_invoiced
                            )
                            if works:
                                exact_match = works.filtered(lambda w: w.work_cost == line.price_unit)
                                if exact_match:
                                    exact_match[0].is_invoiced = False
                                else:
                                    works[0].is_invoiced = False
        return super(AccountMove, self).unlink()
