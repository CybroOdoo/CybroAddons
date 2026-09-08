# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import date, datetime, timedelta

from odoo import _, api, models
from odoo.exceptions import AccessError


class WmDashboard(models.AbstractModel):
    """Backend controller model aggregating waste management operations dashboard metrics."""
    _name = 'wm.dashboard'
    _description = 'Waste Management Dashboard'

    @api.model
    def _get_order_date_domain(self, start_dt, end_dt):
        """
        Return domain matching collection orders scheduled within the period,
        or orders created within the period if scheduled_start was left unset.
        """
        return [
            '|',
            '&', ('scheduled_start', '>=', start_dt), ('scheduled_start', '<=', end_dt),
            '&', ('scheduled_start', '=', False), '&', ('create_date', '>=', start_dt), ('create_date', '<=', end_dt),
        ]

    @api.model
    def get_dashboard_data(self, timeframe='today'):
        """ Return all KPI data needed by the dashboard OWL component filtered by timeframe. """
        authorized_groups = (
            'wm_base.group_wm_dispatcher',
            'wm_base.group_wm_finance',
            'wm_base.group_wm_compliance_officer',
            'wm_base.group_wm_ops_manager',
            'wm_base.group_wm_admin',
        )
        if not (self.env.is_admin() or any(self.env.user.has_group(group) for group in authorized_groups)):
            raise AccessError(_("You do not have access to the Waste Management Dashboard."))

        has_collection = 'wm.collection.order' in self.env.registry
        has_inspection = 'wm.batch.inspection' in self.env.registry
        has_recycling = 'recycling.order' in self.env.registry
        has_fleet = 'fleet.vehicle' in self.env.registry
        has_account = 'account.move' in self.env.registry

        can_access_collection = has_collection and self.env['wm.collection.order'].has_access('read')
        can_access_inspection = has_inspection and self.env['wm.batch.inspection'].has_access('read')
        can_access_recycling = has_recycling and self.env['recycling.order'].has_access('read')
        can_access_product = self.env['product.template'].has_access('read')
        can_access_fleet = has_fleet and self.env['fleet.vehicle'].has_access('read')
        can_access_account = has_account and self.env['account.move'].has_access('read')

        is_admin_or_ops = self.env.user.has_group('wm_base.group_wm_admin') or self.env.user.has_group('wm_base.group_wm_ops_manager')
        is_restricted_role = (
            self.env.user.has_group('wm_base.group_wm_finance') or
            self.env.user.has_group('wm_base.group_wm_compliance_officer') or
            self.env.user.has_group('wm_base.group_wm_dispatcher') or
            self.env.user.has_group('wm_contracts_billing.group_wm_contract_manager')
        )
        can_interact_collection = can_access_collection and not (is_restricted_role and not is_admin_or_ops)

        company_ids = self.env.companies.ids or [self.env.company.id]
        company_domain = ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]

        self = self.sudo()
        Category = self.env['wm.waste.category']
        Material = self.env['wm.waste.material']
        Product = self.env['product.product']

        all_prods = Product.search([('is_waste_material', '=', True)])
        all_wm_mats = Material.search([('active', '=', True)])

        total_categories = Category.search_count([('active', '=', True)])
        total_materials = len(all_prods) + len(all_wm_mats)
        hazardous_count = len(all_prods.filtered(lambda p: p.hazardous)) + len(all_wm_mats.filtered(lambda m: m.hazardous))
        recyclable_count = len(all_prods.filtered(lambda p: p.recyclable)) + len(all_wm_mats.filtered(lambda m: m.recyclable))
        critical_count = len(all_prods.filtered(lambda p: p.hazardous and not p.recyclable)) + len(all_wm_mats.filtered(lambda m: m.hazardous and not m.recyclable))
        safe_count = len(all_prods.filtered(lambda p: not p.hazardous and p.recyclable)) + len(all_wm_mats.filtered(lambda m: not m.hazardous and m.recyclable))
        archived_categories = Category.search_count([('active', '=', False)])
        archived_materials = Material.search_count([('active', '=', False)])

        # Pre-group products and materials by category ID to eliminate N+1 queries
        prods_by_cat = {}
        for p in all_prods:
            cid = p.wm_waste_category_id.id if p.wm_waste_category_id else False
            if cid:
                prods_by_cat.setdefault(cid, []).append(p)

        mats_by_cat = {}
        for m in all_wm_mats:
            cat_ids = set()
            if m.category_id:
                cat_ids.add(m.category_id.id)
            if m.category_ids:
                cat_ids.update(m.category_ids.ids)
            for cid in cat_ids:
                mats_by_cat.setdefault(cid, []).append(m)

        categories = Category.search([('active', '=', True)], order='name asc')
        category_data = []
        for cat in categories:
            prods = prods_by_cat.get(cat.id, [])
            wm_mats = mats_by_cat.get(cat.id, [])

            mat_total = len(prods) + len(wm_mats)
            mat_hazardous = sum(1 for p in prods if p.hazardous) + sum(1 for m in wm_mats if m.hazardous)
            mat_recyclable = sum(1 for p in prods if p.recyclable) + sum(1 for m in wm_mats if m.recyclable)
            mat_non_rec_haz = sum(1 for p in prods if p.hazardous and not p.recyclable) + sum(1 for m in wm_mats if m.hazardous and not m.recyclable)

            category_data.append({
                'id': cat.id,
                'name': cat.name,
                'code': cat.code or (cat.name[:3].upper() if cat.name else ''),
                'total': mat_total,
                'hazardous': mat_hazardous,
                'recyclable': mat_recyclable,
                'non_recyclable_hazardous': mat_non_rec_haz,
            })

        category_data.sort(key=lambda x: x['total'], reverse=True)

        today = date.today()
        today_end = datetime.combine(today, datetime.max.time())

        # Determine start date boundary based on timeframe filter
        if timeframe == 'week':
            start_dt = datetime.combine(today - timedelta(days=6), datetime.min.time())
            prior_start_dt = datetime.combine(today - timedelta(days=13), datetime.min.time())
            prior_end_dt = datetime.combine(today - timedelta(days=7), datetime.max.time())
        elif timeframe == 'month':
            cur_month_start = date(today.year, today.month, 1)
            start_dt = datetime.combine(cur_month_start, datetime.min.time())
            prior_end_date = cur_month_start - timedelta(days=1)
            prior_start_date = date(prior_end_date.year, prior_end_date.month, 1)
            prior_start_dt = datetime.combine(prior_start_date, datetime.min.time())
            prior_end_dt = datetime.combine(prior_end_date, datetime.max.time())
        else: # today
            start_dt = datetime.combine(today, datetime.min.time())
            prior_start_dt = datetime.combine(today - timedelta(days=1), datetime.min.time())
            prior_end_dt = datetime.combine(today - timedelta(days=1), datetime.max.time())

        # 1. Daily Tonnage Collected
        tonnage_labels = []
        tonnage_today = []
        tonnage_last_week = []
        category_names = [cat.name for cat in categories]

        if has_collection:
            today_orders = self.env['wm.collection.order'].search(
                self._get_order_date_domain(start_dt, today_end) +
                [('state', 'not in', ('draft', 'missed'))] +
                company_domain
            )
            last_week_orders = self.env['wm.collection.order'].search(
                self._get_order_date_domain(prior_start_dt, prior_end_dt) +
                [('state', 'not in', ('draft', 'missed'))] +
                company_domain
            )

            today_weight_by_cat = {}
            for order in today_orders:
                for line in order.order_line_ids:
                    cat = line.category_id or (line.product_id.wm_waste_category_id if line.product_id else False)
                    if cat:
                        weight = line.weight or line.estimated_weight or 0.0
                        today_weight_by_cat[cat.name] = today_weight_by_cat.get(cat.name, 0.0) + weight

            last_week_weight_by_cat = {}
            for order in last_week_orders:
                for line in order.order_line_ids:
                    cat = line.category_id or (line.product_id.wm_waste_category_id if line.product_id else False)
                    if cat:
                        weight = line.weight or line.estimated_weight or 0.0
                        last_week_weight_by_cat[cat.name] = last_week_weight_by_cat.get(cat.name, 0.0) + weight

            for cat_name in category_names:
                tonnage_labels.append(cat_name)
                tonnage_today.append(round(today_weight_by_cat.get(cat_name, 0.0), 1))
                tonnage_last_week.append(round(last_week_weight_by_cat.get(cat_name, 0.0), 1))

            # Build stream_distribution: time-filtered tonnage per category for donut chart
            stream_distribution = []
            for cat in categories:
                t = round(today_weight_by_cat.get(cat.name, 0.0), 1)
                if t > 0:
                    stream_distribution.append({
                        'id': cat.id,
                        'name': cat.name,
                        'code': cat.code or cat.name[:3].upper(),
                        'tonnage': t,
                    })
            # If no collection data for this period, fall back to catalogue material counts
            if not stream_distribution:
                stream_distribution = [
                    {
                        'id': cd['id'], 'name': cd['name'],
                        'code': cd['code'], 'tonnage': cd['total'],
                    }
                    for cd in category_data if cd['total'] > 0
                ]
        else:
            tonnage_labels = category_names or ['Plastic', 'Paper', 'Organic', 'Glass', 'Metal']
            tonnage_today = [0.0] * len(tonnage_labels)
            tonnage_last_week = [0.0] * len(tonnage_labels)
            # No collection module: fall back to catalogue material counts
            stream_distribution = [
                {
                    'id': cd['id'], 'name': cd['name'],
                    'code': cd['code'], 'tonnage': cd['total'],
                }
                for cd in category_data if cd['total'] > 0
            ]

        # 2. Active Routes Counter
        if has_collection:
            CollectionOrder = self.env['wm.collection.order']
            base_domain = self._get_order_date_domain(start_dt, today_end) + company_domain
            pending_count = CollectionOrder.search_count(base_domain + [('state', 'in', ('draft', 'scheduled'))])
            in_progress_count = CollectionOrder.search_count(base_domain + [('state', 'in', ('dispatched', 'in_progress'))])
            completed_count = CollectionOrder.search_count(base_domain + [('state', 'in', ('completed', 'signed', 'invoiced'))])
        else:
            pending_count = 0
            in_progress_count = 0
            completed_count = 0

        # 3. Fleet Status
        available_vehicle_ids = []
        dispatched_vehicle_ids_list = []
        maintenance_vehicle_ids_list = []

        if has_fleet:
            fleet_company = company_domain if 'company_id' in self.env['fleet.vehicle']._fields else []
            vehicles = self.env['fleet.vehicle'].search(fleet_company)
            if vehicles:
                in_maint_vehicle_ids = set()
                if 'fleet.vehicle.log.services' in self.env.registry:
                    running_services = self.env['fleet.vehicle.log.services'].search([
                        ('vehicle_id', 'in', vehicles.ids),
                        ('state', '=', 'running')
                    ])
                    in_maint_vehicle_ids.update(running_services.mapped('vehicle_id.id'))

                dispatched_vehicle_ids = set()
                if has_collection:
                    active_date_domain = [
                        '|',
                        ('scheduled_start', '>=', start_dt),
                        '&', ('scheduled_start', '=', False), ('create_date', '>=', start_dt),
                    ]
                    active_orders = self.env['wm.collection.order'].search([
                        ('vehicle_id', 'in', vehicles.ids),
                        ('state', 'in', ('dispatched', 'in_progress'))
                    ] + active_date_domain + company_domain)
                    dispatched_vehicle_ids.update(active_orders.mapped('vehicle_id.id'))

                for vehicle in vehicles:
                    state_name = (vehicle.state_id.name or '').lower() if vehicle.state_id else ''
                    is_wm_maint = (getattr(vehicle, 'state', False) == 'maintenance')

                    if vehicle.id in in_maint_vehicle_ids or is_wm_maint or 'maintenance' in state_name or 'repair' in state_name or 'service' in state_name:
                        maintenance_vehicle_ids_list.append(vehicle.id)
                    elif vehicle.id in dispatched_vehicle_ids or 'dispatch' in state_name or 'progress' in state_name:
                        dispatched_vehicle_ids_list.append(vehicle.id)
                    else:
                        available_vehicle_ids.append(vehicle.id)

        available_count = len(available_vehicle_ids)
        dispatched_count = len(dispatched_vehicle_ids_list)
        maintenance_count = len(maintenance_vehicle_ids_list)

        # 4. Compliance Alerts - Orders Awaiting Signature
        open_manifests = []
        if has_collection:
            awaiting_signature = self.env['wm.collection.order'].search([
                ('state', 'in', ('completed', 'in_progress', 'scheduled'))
            ] + company_domain, order='create_date desc', limit=50)
            open_manifests = [{
                'id': o.id,
                'name': o.name,
                'partner': o.partner_id.name or 'Unknown Partner',
                'date': o.scheduled_start.strftime('%Y-%m-%d') if o.scheduled_start else (o.create_date.strftime('%Y-%m-%d') if o.create_date else '')
            } for o in awaiting_signature]

        # 5. Revenue Tile — tracked per source so frontend drilldowns match exactly
        cur_invoice_revenue = 0.0
        cur_collection_revenue = 0.0
        cur_recycling_revenue = 0.0
        prior_period_revenue = 0.0

        # Store the exact date strings used so the frontend can build matching domains
        start_date_str = start_dt.date().strftime('%Y-%m-%d')
        today_date_str = today_end.date().strftime('%Y-%m-%d')
        start_dt_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
        today_end_str = today_end.strftime('%Y-%m-%d %H:%M:%S')

        # 5.1 Account Move (Customer Invoices & Credit Notes)
        if has_account:
            cur_invoices = self.env['account.move'].search([
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', start_dt.date()),
                ('invoice_date', '<=', today_end.date()),
            ] + company_domain)
            cur_invoice_revenue = sum(
                (inv.amount_untaxed_signed if inv.amount_untaxed_signed is not False else inv.amount_total_signed) or 0.0
                for inv in cur_invoices
            )

            prior_invoices = self.env['account.move'].search([
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'posted'),
                ('invoice_date', '>=', prior_start_dt.date()),
                ('invoice_date', '<=', prior_end_dt.date()),
            ] + company_domain)
            prior_period_revenue += sum(
                (inv.amount_untaxed_signed if inv.amount_untaxed_signed is not False else inv.amount_total_signed) or 0.0
                for inv in prior_invoices
            )

        # 5.2 Collection Orders (Operational unbilled completed/active orders)
        if has_collection:
            order_state_filter = ('completed', 'signed', 'in_progress') if has_account else ('completed', 'signed', 'invoiced', 'in_progress')
            cur_orders = self.env['wm.collection.order'].search(
                self._get_order_date_domain(start_dt, today_end) +
                [('state', 'in', order_state_filter)] +
                company_domain
            )
            cur_collection_revenue = sum(
                (o.total_amount if hasattr(o, 'total_amount') and o.total_amount is not None else sum(l.total_amount or (l.price * (l.weight or l.estimated_weight)) for l in o.order_line_ids))
                if o.order_line_ids or getattr(o, 'total_amount', 0.0) else 0.0
                for o in cur_orders
            )

            prior_orders = self.env['wm.collection.order'].search(
                self._get_order_date_domain(prior_start_dt, prior_end_dt) +
                [('state', 'in', order_state_filter)] +
                company_domain
            )
            prior_order_rev = sum(
                (o.total_amount if hasattr(o, 'total_amount') and o.total_amount is not None else sum(l.total_amount or (l.price * (l.weight or l.estimated_weight)) for l in o.order_line_ids))
                if o.order_line_ids or getattr(o, 'total_amount', 0.0) else 0.0
                for o in prior_orders
            )
            prior_period_revenue += prior_order_rev

        # 5.3 Recycling Revenue
        if has_recycling:
            rec_company = company_domain if 'company_id' in self.env['recycling.order']._fields else []
            cur_recycling = self.env['recycling.order'].search([
                ('state', '=', 'done'),
                ('date_done', '>=', start_dt),
                ('date_done', '<=', today_end),
            ] + rec_company)
            cur_recycling_revenue = sum(cur_recycling.mapped('total_recovered_value'))

            prior_recycling = self.env['recycling.order'].search([
                ('state', '=', 'done'),
                ('date_done', '>=', prior_start_dt),
                ('date_done', '<=', prior_end_dt),
            ] + rec_company)
            prior_period_revenue += sum(prior_recycling.mapped('total_recovered_value'))

        cur_period_revenue = cur_invoice_revenue + cur_collection_revenue + cur_recycling_revenue

        # 6. Collection Efficiency
        efficiency_on_time_ids = []
        efficiency_late_ids = []
        if has_collection:
            completed_orders = self.env['wm.collection.order'].search(
                self._get_order_date_domain(start_dt, today_end) +
                [
                    ('state', 'in', ('completed', 'signed', 'invoiced')),
                    ('actual_end', '!=', False),
                    ('scheduled_end', '!=', False)
                ] + company_domain
            )
            for order in completed_orders:
                if order.actual_end <= order.scheduled_end:
                    efficiency_on_time_ids.append(order.id)
                else:
                    efficiency_late_ids.append(order.id)

            on_time_count = len(efficiency_on_time_ids)
            delayed_count = len(efficiency_late_ids)
            total_completed = on_time_count + delayed_count
            if total_completed > 0:
                on_time_pct = round((on_time_count / total_completed) * 100, 1)
                delayed_pct = round(100.0 - on_time_pct, 1)
            else:
                on_time_pct = 0.0
                delayed_pct = 0.0
        else:
            on_time_pct = 0.0
            delayed_pct = 0.0

        # ---- 10. Batch Inspection Pass/Fail ----
        inspection_passed = 0
        inspection_failed = 0
        inspection_pending = 0
        inspection_pass_rate = 0.0
        recent_failed_inspections = []

        if has_inspection:
            Inspection = self.env['wm.batch.inspection']
            insp_company = company_domain if 'company_id' in Inspection._fields else []
            inspection_passed = Inspection.search_count([
                ('inspection_date', '>=', start_dt),
                ('inspection_date', '<=', today_end),
                ('state', '=', 'passed'),
            ] + insp_company)
            inspection_failed = Inspection.search_count([
                ('inspection_date', '>=', start_dt),
                ('inspection_date', '<=', today_end),
                ('state', '=', 'failed'),
            ] + insp_company)
            inspection_pending = Inspection.search_count([
                ('inspection_date', '>=', start_dt),
                ('inspection_date', '<=', today_end),
                ('state', 'in', ('draft', 'in_progress')),
            ] + insp_company)

            decided_total = inspection_passed + inspection_failed
            if decided_total:
                inspection_pass_rate = round(inspection_passed / decided_total * 100, 1)
            else:
                inspection_pass_rate = 0.0

            recent_failed = Inspection.search(
                [('state', '=', 'failed'), ('inspection_date', '>=', start_dt)] + insp_company,
                order='inspection_date desc', limit=10
            )
            recent_failed_inspections = [{
                'id': i.id,
                'name': i.name,
                'batch': i.batch_id.name or '—',
                'contamination': round(i.contamination_percentage, 1),
                'date': i.inspection_date.strftime('%Y-%m-%d %H:%M') if i.inspection_date else '',
            } for i in recent_failed]

        # ---- 11. Waste Batch Recycling ----
        recycling_avg_recovery_rate = 0.0
        recycling_value_mtd = 0.0
        recycling_orders_done_count = 0
        recycling_category_rates = []
        top_recovered_materials = []

        if has_recycling:
            Recycling = self.env['recycling.order']
            RecyclingLine = self.env['recycling.line']

            done_orders = Recycling.search([
                ('state', '=', 'done'),
                ('date_done', '>=', start_dt),
                ('date_done', '<=', today_end),
            ])
            recycling_orders_done_count = len(done_orders)
            if done_orders:
                recycling_avg_recovery_rate = round(
                    sum(done_orders.mapped('overall_recovery_rate')) / len(done_orders), 1
                )
            recycling_value_mtd = round(sum(done_orders.mapped('total_recovered_value')), 2)

            for cat in categories:
                cat_orders = done_orders.filtered(lambda o: o.category_id.id == cat.id)
                if cat_orders:
                    recycling_category_rates.append({
                        'code': cat.code,
                        'name': cat.name,
                        'recovery_rate': round(
                            sum(cat_orders.mapped('overall_recovery_rate')) / len(cat_orders), 1
                        ),
                    })

            month_lines = RecyclingLine.search([
                ('order_id.state', '=', 'done'),
                ('order_id.date_done', '>=', start_dt),
                ('order_id.date_done', '<=', today_end),
            ], order='line_value desc', limit=5)
            top_recovered_materials = [{
                'order_id': l.order_id.id,
                'product': l.product_id.display_name or '—',
                'recovered_qty': round(l.recovered_qty, 2),
                'uom': l.uom_id.name or '',
                'recovery_rate': round(l.recovery_rate, 1),
                'line_value': round(l.line_value, 2),
            } for l in month_lines]

        return {
            'total_categories': total_categories,
            'total_materials': total_materials,
            'hazardous_count': hazardous_count,
            'recyclable_count': recyclable_count,
            'critical_count': critical_count,
            'safe_count': safe_count,
            'archived_categories': archived_categories,
            'archived_materials': archived_materials,
            'hazardous_pct': round(
                (hazardous_count / total_materials * 100) if total_materials else 0, 1
            ),
            'recyclable_pct': round(
                (recyclable_count / total_materials * 100) if total_materials else 0, 1
            ),
            'category_data': category_data,
            'stream_distribution': stream_distribution,
            'tonnage_labels': tonnage_labels,
            'tonnage_today': tonnage_today,
            'tonnage_last_week': tonnage_last_week,
            'pending_count': pending_count,
            'in_progress_count': in_progress_count,
            'completed_count': completed_count,
            'fleet_available': available_count,
            'fleet_dispatched': dispatched_count,
            'fleet_maintenance': maintenance_count,
            'fleet_available_ids': available_vehicle_ids,
            'fleet_dispatched_ids': dispatched_vehicle_ids_list,
            'fleet_maintenance_ids': maintenance_vehicle_ids_list,
            'open_manifests': open_manifests,
            'revenue_cur_month': round(cur_period_revenue, 2),
            'revenue_prior_month': round(prior_period_revenue, 2),
            # Revenue breakdown by source — used by frontend drilldown to open matching list
            'revenue_invoice': round(cur_invoice_revenue, 2),
            'revenue_collection': round(cur_collection_revenue, 2),
            'revenue_recycling': round(cur_recycling_revenue, 2),
            # Exact date strings the backend used — frontend uses these for domain to guarantee match
            'revenue_start_date': start_date_str,
            'revenue_end_date': today_date_str,
            'revenue_start_dt': start_dt_str,
            'revenue_end_dt': today_end_str,
            'on_time_pct': on_time_pct,
            'delayed_pct': delayed_pct,
            'efficiency_on_time_ids': efficiency_on_time_ids,
            'efficiency_late_ids': efficiency_late_ids,
            'has_collection': has_collection,
            'has_fleet': has_fleet,

            'has_inspection': has_inspection,
            'inspection_passed': inspection_passed,
            'inspection_failed': inspection_failed,
            'inspection_pending': inspection_pending,
            'inspection_pass_rate': inspection_pass_rate,
            'recent_failed_inspections': recent_failed_inspections,

            'has_recycling': has_recycling,
            'recycling_avg_recovery_rate': recycling_avg_recovery_rate,
            'recycling_value_mtd': recycling_value_mtd,
            'recycling_orders_done_count': recycling_orders_done_count,
            'recycling_category_rates': recycling_category_rates,
            'top_recovered_materials': top_recovered_materials,
            'can_access_collection': can_access_collection,
            'can_interact_collection': can_interact_collection,
            'can_access_inspection': can_access_inspection,
            'can_access_recycling': can_access_recycling,
            'can_access_product': can_access_product,
            'can_access_fleet': can_access_fleet,
            'has_account': has_account,
            'can_access_account': can_access_account,
            'active_timeframe': timeframe,
            'currency_symbol': self.env.company.currency_id.symbol or '$',
        }
