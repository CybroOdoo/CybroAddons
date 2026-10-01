/** @odoo-module **/
import { Component, onWillStart, onWillUpdateProps, useState, markup } from "@odoo/owl";
import { View } from "@web/views/view";
import { useService } from "@web/core/utils/hooks";
import { DashboardCardButtons } from "./dashboard_card_buttons";

export class DashboardActivity extends Component {
    setup() {
        this.actionService = useService("action");
        this.viewService = useService("view");
        this.orm = useService("orm");

        this.state = useState({
            viewProps: null,
            error: null,
            timelineActivities: null,
            feedActivities: null,
            summaryData: null,
            calendarData: null,
            currentWeekStart: null,
            selectedDate: null, // NEW: Track selected date
            rawCalendarActivities: [], // NEW: Store raw data for re-filtering
        });

        onWillStart(async () => {
            // Initialize to current week
            const now = new Date();
            const dayOfWeek = now.getDay();
            this.state.currentWeekStart = new Date(now);
            this.state.currentWeekStart.setDate(now.getDate() - dayOfWeek);
            this.state.currentWeekStart.setHours(0, 0, 0, 0);

            this.state.selectedDate = new Date(); // Default select today
            this.state.selectedDate.setHours(0, 0, 0, 0);

            await this.updateViewProps(this.props);
        });

        onWillUpdateProps(async (nextProps) => {
            await this.updateViewProps(nextProps);
        });
    }

    get viewProps() { return this.state.viewProps; }
    get error() { return this.state.error; }
    get timelineActivities() { return this.state.timelineActivities; }
    get feedActivities() { return this.state.feedActivities; }
    get summaryData() { return this.state.summaryData; }
    get calendarData() { return this.state.calendarData; }

    hasData() {
        const type = this.props.card.activity_type;
        if (type === 'timeline') {
            if (!this.state.timelineActivities) return false;
            return Object.values(this.state.timelineActivities).some(arr => arr && arr.length > 0);
        }
        if (type === 'feed') {
            return this.state.feedActivities && this.state.feedActivities.length > 0;
        }
        if (type === 'summary') {
            return this.state.summaryData && this.state.summaryData.stats.total > 0;
        }
        if (type === 'calendar') {
            // Check raw activities or week days? Raw is safer for "no data at all"
            // But calendar always shows days. Let's check if there are ANY activities in the period.
            return this.state.rawCalendarActivities && this.state.rawCalendarActivities.length > 0;
        }
        return false;
    }

    getMarkup(content) {
        return content ? markup(content) : "";
    }

    async updateViewProps(props) {
        this.state.error = null;
        if (!props.card || !props.card.model_name) {
            this.state.viewProps = null;
            return;
        }

        const activityType = props.card.activity_type || 'summary';

        // 1. Build domain for the target model (e.g. sale.order)
        const targetModelDomain = this.getTargetModelDomain(props);

        // 2. Build domain for the activity model (mail.activity)
        const activityModelDomain = this.getActivityModelDomain(props);

        let finalDomain = [['res_model', '=', props.card.model_name], ...activityModelDomain];

        try {
            // 3. If target model domain is present, search for matching record IDs
            if (targetModelDomain.length > 0) {
                const matchingRecordIds = await this.orm.search(props.card.model_name, targetModelDomain);
                finalDomain.push(['res_id', 'in', matchingRecordIds]);
            }

            if (activityType === 'timeline') {
                const activities = await this.orm.searchRead(
                    'mail.activity',
                    finalDomain,
                    ['id', 'summary', 'date_deadline', 'activity_type_id', 'user_id', 'res_id', 'res_name', 'state', 'note'],
                    { limit: props.card.record_limit || 50, order: 'date_deadline asc' }
                );
                this.state.timelineActivities = this.groupActivitiesByDate(activities);

            } else if (activityType === 'feed') {
                const activities = await this.orm.searchRead(
                    'mail.activity',
                    finalDomain,
                    ['id', 'summary', 'date_deadline', 'activity_type_id', 'user_id', 'res_id', 'res_name', 'state', 'note', 'create_date'],
                    { limit: props.card.record_limit || 20, order: 'create_date desc' }
                );
                this.state.feedActivities = activities;

            } else if (activityType === 'summary') {
                const activities = await this.orm.searchRead(
                    'mail.activity',
                    finalDomain,
                    ['id', 'summary', 'date_deadline', 'activity_type_id', 'user_id', 'res_id', 'res_name', 'state', 'note', 'create_date'],
                    { limit: 100, order: 'create_date desc' }
                );
                this.state.summaryData = this.computeSummaryData(activities);

            } else if (activityType === 'calendar') {
                const activities = await this.orm.searchRead(
                    'mail.activity',
                    finalDomain,
                    ['id', 'summary', 'date_deadline', 'activity_type_id', 'user_id', 'res_id', 'res_name', 'state'],
                    { limit: props.card.record_limit || 100, order: 'date_deadline asc' }
                );
                this.state.rawCalendarActivities = activities;
                this.state.calendarData = this.computeCalendarData(activities);

            }
            this.state.viewProps = null;
        } catch (e) {
            this.state.error = `Error loading ${activityType} view: ${e.message}`;
            this.state.viewProps = null;

        }
    }

    async previousWeek() {
        if (!this.state.currentWeekStart) return;
        this.state.currentWeekStart.setDate(this.state.currentWeekStart.getDate() - 7);
        // Reset selected date to match the new week's start? Or keep it? 
        // Let's keep it simple: Select the first day of the new week
        this.state.selectedDate = new Date(this.state.currentWeekStart);
        await this.refreshCalendarData();
    }

    async nextWeek() {
        if (!this.state.currentWeekStart) return;
        this.state.currentWeekStart.setDate(this.state.currentWeekStart.getDate() + 7);
        this.state.selectedDate = new Date(this.state.currentWeekStart);
        await this.refreshCalendarData();
    }

    selectDate(dateStr) {
        const newDate = new Date(dateStr);
        newDate.setHours(0, 0, 0, 0);
        this.state.selectedDate = newDate;
        // Recompute using stored raw data
        this.state.calendarData = this.computeCalendarData(this.state.rawCalendarActivities);
    }

    async refreshCalendarData() {
        if (this.props.card.activity_type !== 'calendar') return;

        const targetModelDomain = this.getTargetModelDomain(this.props);
        const activityModelDomain = this.getActivityModelDomain(this.props);

        let finalDomain = [['res_model', '=', this.props.card.model_name], ...activityModelDomain];

        try {
            if (targetModelDomain.length > 0) {
                const matchingRecordIds = await this.orm.search(this.props.card.model_name, targetModelDomain);
                finalDomain.push(['res_id', 'in', matchingRecordIds]);
            }
            const activities = await this.orm.searchRead(
                'mail.activity',
                finalDomain,
                ['id', 'summary', 'date_deadline', 'activity_type_id', 'user_id', 'res_id', 'res_name', 'state'],
                { limit: this.props.card.record_limit || 100, order: 'date_deadline asc' }
            );
            this.state.rawCalendarActivities = activities;
            this.state.calendarData = this.computeCalendarData(activities);
        } catch (e) {
        }
    }

    computeCalendarData(activities) {
        if (!this.state.currentWeekStart) this.state.currentWeekStart = new Date();
        const selected = this.state.selectedDate || new Date();
        selected.setHours(0, 0, 0, 0);

        const weekStart = new Date(this.state.currentWeekStart);
        const weekDays = [];

        for (let i = 0; i < 7; i++) {
            const weekDate = new Date(weekStart);
            weekDate.setDate(weekStart.getDate() + i);
            weekDate.setHours(0, 0, 0, 0);

            const dayActivities = activities.filter(act => {
                if (!act.date_deadline) return false;
                const actDate = new Date(act.date_deadline);
                actDate.setHours(0, 0, 0, 0);
                return actDate.getTime() === weekDate.getTime();
            });

            weekDays.push({
                day: weekDate.getDate(),
                date: weekDate, // Keep as Date object
                isToday: weekDate.toDateString() === new Date().toDateString(),
                isSelected: weekDate.getTime() === selected.getTime(),
                activities: dayActivities,
                dayLabel: weekDate.toLocaleDateString('en-US', { weekday: 'short' }).substring(0, 2)
            });
        }

        // Get activities for Selected Date
        let selectedActivities = activities.filter(act => {
            if (!act.date_deadline) return false;
            const actDate = new Date(act.date_deadline);
            actDate.setHours(0, 0, 0, 0);
            return actDate.getTime() === selected.getTime();
        });

        const midWeek = new Date(weekStart);
        midWeek.setDate(weekStart.getDate() + 3);

        return {
            monthName: midWeek.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
            weekDays: weekDays,
            selectedActivities: selectedActivities, // Renamed from todayActivities
            weekStart: weekStart,
            selectedDateLabel: selected.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })
        };
    }

    computeSummaryData(activities) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        let total = activities.length;
        let dueToday = 0;
        let completed = 0;
        let overdue = 0;

        const typeBreakdown = {};
        const recentActivities = [];

        activities.forEach(activity => {
            if (activity.state === 'done') {
                completed++;
            } else {
                const deadline = new Date(activity.date_deadline);
                deadline.setHours(0, 0, 0, 0);

                if (deadline.getTime() === today.getTime()) {
                    dueToday++;
                } else if (deadline < today) {
                    overdue++;
                }
            }

            const typeName = activity.activity_type_id ? activity.activity_type_id[1] : 'Other';
            typeBreakdown[typeName] = (typeBreakdown[typeName] || 0) + 1;

            if (recentActivities.length < 6) {
                recentActivities.push(activity);
            }
        });

        return {
            stats: { total, dueToday, completed, overdue },
            typeBreakdown: Object.entries(typeBreakdown).sort((a, b) => b[1] - a[1]).slice(0, 5),
            recentActivities
        };
    }

    groupActivitiesByDate(activities) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        const nextWeek = new Date(today);
        nextWeek.setDate(nextWeek.getDate() + 7);

        const groups = { overdue: [], today: [], tomorrow: [], nextWeek: [], later: [] };

        activities.forEach(activity => {
            const deadline = new Date(activity.date_deadline);
            deadline.setHours(0, 0, 0, 0);
            if (activity.state === 'done') activity.completed = true;

            if (deadline < today && activity.state !== 'done') groups.overdue.push(activity);
            else if (deadline.getTime() === today.getTime()) groups.today.push(activity);
            else if (deadline.getTime() === tomorrow.getTime()) groups.tomorrow.push(activity);
            else if (deadline < nextWeek) groups.nextWeek.push(activity);
            else groups.later.push(activity);
        });
        return groups;
    }

    parseDomain(domainStr) {
        if (!domainStr || domainStr === "" || domainStr === "[]") return [];
        try {
            if (Array.isArray(domainStr)) return domainStr;
            let processed = domainStr
                .replace(/\(/g, '[')
                .replace(/\)/g, ']')
                .replace(/'/g, '"')
                .replace(/True/g, 'true')
                .replace(/False/g, 'false')
                .replace(/None/g, 'null');
            return JSON.parse(processed);
        } catch (e) {
            return [];
        }
    }

    getTargetModelDomain(props) {
        try {
            let domain = this.parseDomain(props.card.domain);

            // Apply custom backend filter if present in props
            const customFilterDomain = props.customFilterDomain;
            const customFilterModel = props.customFilterModel;
            const cardModelId = Array.isArray(props.card.model_id) ? props.card.model_id[0] : props.card.model_id;

            if (customFilterModel) {
                if (Number(customFilterModel) !== Number(cardModelId)) {
                    return [['id', '=', -1]];
                }
            }

            if (customFilterDomain) {
                const parsedCustomDomain = this.parseDomain(customFilterDomain);
                if (parsedCustomDomain && parsedCustomDomain.length > 0) {
                    domain = [...domain, ...parsedCustomDomain];
                }
            }
            return domain;
        } catch (e) { return []; }
    }

    getActivityModelDomain(props) {
        try {
            let domain = [];
            const dateFilter = props.dateFilter || 'all';
            if (dateFilter !== 'all') {
                const now = new Date();
                let start, end;
                if (dateFilter === 'this_week') {
                    const dayOfWeek = now.getDay();
                    const diff = now.getDate() - dayOfWeek + (dayOfWeek === 0 ? -6 : 1);
                    start = new Date(now.getFullYear(), now.getMonth(), diff, 0, 0, 0);
                    end = new Date(start);
                    end.setDate(start.getDate() + 6);
                    end.setHours(23, 59, 59);
                } else if (dateFilter === 'this_month') {
                    start = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0);
                    end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);
                } else if (dateFilter === 'today') {
                    start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
                    end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
                } else if (dateFilter === 'this_quarter') {
                    const month = now.getMonth();
                    const quarterStartMonth = Math.floor(month / 3) * 3;
                    start = new Date(now.getFullYear(), quarterStartMonth, 1, 0, 0, 0);
                    end = new Date(now.getFullYear(), quarterStartMonth + 3, 0, 23, 59, 59);
                } else if (dateFilter === 'this_year') {
                    start = new Date(now.getFullYear(), 0, 1, 0, 0, 0);
                    end = new Date(now.getFullYear(), 11, 31, 23, 59, 59);
                } else if (dateFilter === 'custom' && props.customStartDate && props.customEndDate) {
                    start = new Date(props.customStartDate);
                    start.setHours(0, 0, 0, 0);
                    end = new Date(props.customEndDate);
                    end.setHours(23, 59, 59);
                }

                if (start && end) {
                    const formatDate = (date) => {
                        const year = date.getFullYear();
                        const month = String(date.getMonth() + 1).padStart(2, '0');
                        const day = String(date.getDate()).padStart(2, '0');
                        const hours = String(date.getHours()).padStart(2, '0');
                        const minutes = String(date.getMinutes()).padStart(2, '0');
                        const seconds = String(date.getSeconds()).padStart(2, '0');
                        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
                    };
                    domain.push(['create_date', '>=', formatDate(start)]);
                    domain.push(['create_date', '<=', formatDate(end)]);
                }
            }
            return domain;
        } catch (e) { return []; }
    }

    getActivityTypeLabel(activityTypeId) {
        if (!activityTypeId) return 'Task';
        return activityTypeId[1] || 'Task';
    }

    getActivityTypeClass(activityTypeId) {
        if (!activityTypeId) return '';
        const typeName = activityTypeId[1] ? activityTypeId[1].toLowerCase() : '';
        if (typeName.includes('call')) return 'call';
        if (typeName.includes('meeting')) return 'meeting';
        if (typeName.includes('email')) return 'email';
        return '';
    }

    getActivityTypeColor(activityTypeId) {
        if (!activityTypeId) return '#3b82f6'; // Default Blue
        const typeName = activityTypeId[1] ? activityTypeId[1].toLowerCase() : '';
        if (typeName.includes('call')) return '#2563eb'; // Deep Blue
        if (typeName.includes('meeting')) return '#3b82f6'; // Bright Blue
        if (typeName.includes('email')) return '#60a5fa'; // Light Blue
        if (typeName.includes('todo') || typeName.includes('task')) return '#1d4ed8'; // Indigo Blue
        return '#3b82f6'; // Default Blue
    }

    getActivityIcon(activityTypeId) {
        if (!activityTypeId) return '📋';
        const typeName = activityTypeId[1] ? activityTypeId[1].toLowerCase() : '';
        if (typeName.includes('call')) return '📞';
        if (typeName.includes('meeting')) return '🤝';
        if (typeName.includes('email')) return '📧';
        if (typeName.includes('todo') || typeName.includes('task')) return '✅';
        return '📋';
    }

    getActivityIconClass(activityTypeId) {
        if (!activityTypeId) return 'fas fa-clipboard-list';
        const typeName = activityTypeId[1] ? activityTypeId[1].toLowerCase() : '';
        if (typeName.includes('call')) return 'fas fa-phone-alt';
        if (typeName.includes('meeting')) return 'fas fa-handshake';
        if (typeName.includes('email')) return 'fas fa-envelope';
        if (typeName.includes('upload')) return 'fas fa-folder-open';
        if (typeName.includes('todo') || typeName.includes('task')) return 'fas fa-check-square';
        return 'fas fa-clipboard-list';
    }

    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }

    formatTime(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
    }

    getRelativeTime(dateStr) {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays}d ago`;
        return this.formatDate(dateStr);
    }

    getOverdueDays(dateStr) {
        const deadline = new Date(dateStr);
        const today = new Date();
        const diffTime = today - deadline;
        return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    }

    onActivityClick(activity) {
        if (!this.props.card.enable_click) return;
        if (activity.res_id) {
            this.actionService.doAction({
                type: "ir.actions.act_window",
                name: activity.res_name || this.props.card.model_name,
                res_model: this.props.card.model_name,
                res_id: activity.res_id,
                view_mode: "form",
                views: [[false, "form"]],
                target: "current",
            });
        }
    }
}

DashboardActivity.template = "odoo_dynamic_dashboard.DashboardActivityCard";
DashboardActivity.components = { DashboardCardButtons, View };