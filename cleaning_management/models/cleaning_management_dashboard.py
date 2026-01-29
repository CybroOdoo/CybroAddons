# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
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
#############################################################################
from odoo import fields, models
from odoo.tools import date_utils


class CleaningManagementDashBoard(models.Model):
    """Creating new model to extract counts for bookings, cleanings,
    and dirty states, intended for visualization on a dashboard."""
    _name = "cleaning.management.dashboard"
    _description = "Cleaning Management Dashboard"

    def get_dashboard_count(self):
        """Getting count of bookings,teams,cleaning and dirty count"""
        bookings = self.env['cleaning.booking'].search_count([
            ('state', '=', 'booked')])
        teams = self.env['cleaning.team'].search_count([])
        cleaning_counts = self.env['cleaning.inspection'].search_count([
            ('state', '=', 'cleaned')])
        dirty_counts = self.env['cleaning.inspection'].search_count([
            ('state', '=', 'dirty')])
        values = {
            'bookings': bookings,
            'teams': teams,
            'cleaned': cleaning_counts,
            'dirty': dirty_counts
        }
        return values

    def get_the_booking_year(self):
        """Get year wise booking"""
        cleaning = self.env['cleaning.booking']
        total_booking_stage_year = cleaning.search([]).filtered(
            lambda l: l.booking_date.year == fields.date.today().year).mapped(
            'state')
        year_stage = [*set(total_booking_stage_year)]
        order_of_stages = ['draft', 'booked', 'cleaned', 'cancelled']
        # Sort the stages based on the predefined order
        sorted_stages = sorted(year_stage,
                               key=lambda x: order_of_stages.index(x))
        year_booking_stages = [stage.capitalize() for stage in sorted_stages]
        total_booking_stage_draft_year = cleaning.search([
            ('state', '=', 'draft')]).filtered(
            lambda l: l.booking_date.year == fields.date.today().year)
        total_booking_stage_booked_year = cleaning.search([
            ('state', '=', 'booked')]).filtered(
            lambda l: l.booking_date.year == fields.date.today().year)
        total_booking_stage_cleaned_year = cleaning.search([
            ('state', '=', 'cleaned')]).filtered(
            lambda l: l.booking_date.year == fields.date.today().year)
        total_booking_stage_canceled_year = cleaning.search([
            ('state', '=', 'cancelled')]).filtered(
            lambda l: l.booking_date.year == fields.date.today().year)
        return {
            'total_booking_stage_year': year_booking_stages,
            'total_booking_stage_draft_year': len(
                total_booking_stage_draft_year),
            'total_booking_stage_booked_year': len(
                total_booking_stage_booked_year),
            'total_booking_stage_cleaned_year': len(
                total_booking_stage_cleaned_year),
            'total_booking_stage_canceled_year': len(
                total_booking_stage_canceled_year)
        }

    def get_the_booking_month(self):
        """Get month wise booking"""
        cleaning = self.env['cleaning.booking']
        total_booking_stage_month = cleaning.search([]).filtered(
            lambda l: l.booking_date.month == fields.date.today().month).mapped(
            'state')
        month_stage = [*set(total_booking_stage_month)]
        order_of_stages = ['draft', 'booked', 'cleaned', 'cancelled']
        # Sort the stages based on the predefined order
        sorted_stages = sorted(month_stage,
                               key=lambda x: order_of_stages.index(x))
        monthly_booking_stages = [stage.capitalize() for stage in sorted_stages]
        total_booking_stage_draft_month = cleaning.search(
            [('state', '=', 'draft')]).filtered(
            lambda l: l.booking_date.month == fields.date.today().month)
        total_booking_stage_booked_month = cleaning.search([
            ('state', '=', 'booked')]).filtered(
            lambda l: l.booking_date.month == fields.date.today().month)
        total_booking_stage_cleaned_month = cleaning.search([
            ('state', '=', 'cleaned')]).filtered(
            lambda l: l.booking_date.month == fields.date.today().month)
        total_booking_stage_canceled_month = cleaning.search([
            ('state', '=', 'cancelled')]).filtered(
            lambda l: l.booking_date.month == fields.date.today().month)
        return {
            'total_booking_stage_month': monthly_booking_stages,
            'total_booking_stage_draft_month': len(
                total_booking_stage_draft_month),
            'total_booking_stage_booked_month': len(
                total_booking_stage_booked_month),
            'total_booking_stage_cleaned_month': len(
                total_booking_stage_cleaned_month),
            'total_booking_stage_canceled_month': len(
                total_booking_stage_canceled_month),
        }

    def get_the_booking_week(self):
        """Get week wise booking"""
        cleaning = self.env['cleaning.booking']
        total_booking_stage_week = cleaning.search([]).filtered(
            lambda l: l.booking_date.isocalendar()[1] ==
                      fields.date.today().isocalendar()[1]).mapped('state')
        week_stage = [*set(total_booking_stage_week)]
        order_of_stages = ['draft', 'booked', 'cleaned', 'cancelled']
        # Sort the stages based on the predefined order
        sorted_stages = sorted(week_stage,
                               key=lambda x: order_of_stages.index(x))
        weekly_booking_stages = [stage.capitalize() for stage in sorted_stages]
        total_booking_stage_draft_week = cleaning.search([
            ('state', '=', 'draft')]).filtered(
            lambda l: l.booking_date.isocalendar()[1] ==
                      fields.date.today().isocalendar()[1])
        total_booking_stage_booked_week = cleaning.search([
            ('state', '=', 'booked')]).filtered(
            lambda l: l.booking_date.isocalendar()[1] ==
                      fields.date.today().isocalendar()[1])
        total_booking_stage_cleaned_week = cleaning.search([
            ('state', '=', 'cleaned')]).filtered(
            lambda l: l.booking_date.isocalendar()[1] ==
                      fields.date.today().isocalendar()[1])
        total_booking_stage_canceled_week = cleaning.search([
            ('state', '=', 'cancelled')]).filtered(
            lambda l: l.booking_date.isocalendar()[1] ==
                      fields.date.today().isocalendar()[1])
        return {
            'total_booking_stage_week': weekly_booking_stages,
            'total_booking_stage_draft_week': len(
                total_booking_stage_draft_week),
            'total_booking_stage_booked_week': len(
                total_booking_stage_booked_week),
            'total_booking_stage_cleaned_week': len(
                total_booking_stage_cleaned_week),
            'total_booking_stage_canceled_week': len(
                total_booking_stage_canceled_week),
        }

    def get_the_booking_quarter(self):
        """Get quarter wise booking"""
        cleaning = self.env['cleaning.booking']
        start_date, end_date = date_utils.get_quarter(fields.date.today())
        total_booking_stage_quarter = cleaning.search([]).filtered(
            lambda l: start_date <= l.booking_date <= end_date).mapped('state')
        quarter_stage = [*set(total_booking_stage_quarter)]
        order_of_stages = ['draft', 'booked', 'cleaned', 'cancelled']
        # Sort the stages based on the predefined order
        sorted_stages = sorted(quarter_stage,
                               key=lambda x: order_of_stages.index(x))
        quarterly_booking_stages = [stage.capitalize() for stage in sorted_stages]
        total_booking_stage_draft_quarter = cleaning.search([
            ('state', '=', 'draft')]).filtered(
            lambda l: start_date <= l.booking_date <= end_date)
        total_booking_stage_booked_quarter = cleaning.search([
            ('state', '=', 'booked')]).filtered(
            lambda l: start_date <= l.booking_date <= end_date)
        total_booking_stage_cleaned_quarter = cleaning.search([
            ('state', '=', 'cleaned')]).filtered(
            lambda l: start_date <= l.booking_date <= end_date)
        total_booking_stage_canceled_quarter = cleaning.search([
            ('state', '=', 'cancelled')]).filtered(
            lambda l: start_date <= l.booking_date <= end_date)
        return {
            'total_booking_stage_quarter': quarterly_booking_stages,
            'total_booking_stage_draft_quarter': len(
                total_booking_stage_draft_quarter),
            'total_booking_stage_booked_quarter': len(
                total_booking_stage_booked_quarter),
            'total_booking_stage_cleaned_quarter': len(
                total_booking_stage_cleaned_quarter),
            'total_booking_stage_canceled_quarter': len(
                total_booking_stage_canceled_quarter),
        }

    def quality_year(self):
        """Get year wise quality of cleaning"""
        quality = self.env['cleaning.inspection']
        quality_year = quality.search([]).filtered(
            lambda
                l: l.inspection_date_and_time.year == fields.date.today().year).mapped(
            'state')
        year_stage = [*set(quality_year)]
        order_of_stages = ['cleaned', 'dirty']
        # Sort the stages based on the predefined order
        sorted_stages = sorted(year_stage,
                               key=lambda x: order_of_stages.index(x))
        yearly_quality_stages = [stage.capitalize() for stage in sorted_stages]
        cleaned_quality_year = quality.search([
            ('state', '=', 'cleaned')]).filtered(
            lambda
                l: l.inspection_date_and_time.year == fields.date.today().year)
        dirty_quality_year = quality.search([('state', '=', 'dirty')]).filtered(
            lambda
                l: l.inspection_date_and_time.year == fields.date.today().year)
        return {
            'quality_year': yearly_quality_stages,
            'cleaned_quality_year': len(cleaned_quality_year),
            'dirty_quality_year': len(dirty_quality_year)
        }

    def quality_month(self):
        """Get month wise quality of cleaning"""
        quality = self.env['cleaning.inspection'].search([])
        quality_month = quality.search([]).filtered(
            lambda
                l: l.inspection_date_and_time.month == fields.date.today().month).mapped(
            'state')
        month_stage = [*set(quality_month)]
        order_of_stages = ['cleaned', 'dirty']
        # Sort the stages based on the predefined order
        sorted_stages = sorted(month_stage,
                               key=lambda x: order_of_stages.index(x))
        monthly_quality_stages = [stage.capitalize() for stage in sorted_stages]
        cleaned_quality_month = quality.search([
            ('state', '=', 'cleaned')]).filtered(
            lambda
                l: l.inspection_date_and_time.month == fields.date.today().month)
        dirty_quality_month = quality.search(
            [('state', '=', 'dirty')]).filtered(
            lambda
                l: l.inspection_date_and_time.month == fields.date.today().month)
        return {
            'quality_month': monthly_quality_stages,
            'cleaned_quality_month': len(cleaned_quality_month),
            'dirty_quality_month': len(dirty_quality_month)
        }

    def quality_week(self):
        """Get week wise quality of cleaning"""
        quality = self.env['cleaning.inspection']
        quality_week = quality.search([]).filtered(
            lambda l: l.inspection_date_and_time.isocalendar()[1] ==
                      fields.date.today().isocalendar()[1]).mapped('state')
        week_stage = [*set(quality_week)]
        order_of_stages = ['cleaned', 'dirty']
        # Sort the stages based on the predefined order
        sorted_stages = sorted(week_stage,
                               key=lambda x: order_of_stages.index(x))
        capitalized_stages = [stage.capitalize() for stage in sorted_stages]
        cleaned_quality_week = quality.search([
            ('state', '=', 'cleaned')]).filtered(
            lambda l: l.inspection_date_and_time.isocalendar()[1] ==
                      fields.date.today().isocalendar()[1])
        dirty_quality_week = quality.search([
            ('state', '=', 'dirty')]).filtered(
            lambda l: l.inspection_date_and_time.isocalendar()[1] ==
                      fields.date.today().isocalendar()[1])
        return {
            'quality_week': capitalized_stages,
            'cleaned_quality_week': len(cleaned_quality_week),
            'dirty_quality_week': len(dirty_quality_week)
        }

    def quality_quarter(self):
        """Get quarter wise quality of cleaning"""
        start_date, end_date = date_utils.get_quarter(fields.datetime.today())
        quality = self.env['cleaning.inspection']
        quality_quarter = quality.search([]).filtered(
            lambda
                l: start_date <= l.inspection_date_and_time <= end_date).mapped(
            'state')
        quarter_stage = [*set(quality_quarter)]
        order_of_stages = ['cleaned', 'dirty']
        # Sort the stages based on the predefined order
        sorted_stages = sorted(quarter_stage,
                               key=lambda x: order_of_stages.index(x))
        capitalized_stages = [stage.capitalize() for stage in sorted_stages]
        cleaned_quality_quarter = quality.search([
            ('state', '=', 'cleaned')]).filtered(
            lambda l: start_date <= l.inspection_date_and_time <= end_date)
        dirty_quality_quarter = quality.search([
            ('state', '=', 'dirty')]).filtered(
            lambda l: start_date <= l.inspection_date_and_time <= end_date)
        return {
            'quality_quarter': capitalized_stages,
            'cleaned_quality_quarter': len(cleaned_quality_quarter),
            'dirty_quality_quarter': len(dirty_quality_quarter)
        }

    def cleaning_count(self):
        """Creating a function to retrieve the counts of bookings,
        cleanings, and dirty states."""
        return {
            'bookings': [rec for rec in
                         self.env['cleaning.booking'].search([])],
            'inspections': [rec for rec in
                            self.env['cleaning.inspection'].search([])]
        }
