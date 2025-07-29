/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useRef, onWillUnmount, useState, onWillStart, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";


export class ModuleQuality extends Component {

    setup() {
        super.setup();

        this.orm = useService('orm');
        this.action = useService("action");
        this.notification = useService("notification");
        this.setActiveComponent = this.props.setActiveComponent;

        this.overview = useRef('overview');
        this.overviewText = useRef('overview_text');
        this.selectRef = useRef("select");

        this.state = useState({
            field : {},
            quality_monitoring : {},
            loading: true,
            all_modules : {},
            loading_accordian: false,
            expanded_accordian: false,
            selectedModule: false,
        });

        this.orm = useService("orm");
        this.notification = useService("notification");

        onWillStart(async () => {
            this.moduleLineOfCode();
            this.getAllModulesAndIcon();
            this.countFields();
            this.state.selectedAuthor = null;
        });
        useEffect(() => {
            this.renderOverviewChart();
        });

    }

    // lines of code in modules
    async moduleLineOfCode() {
        this.orm.call("module.quality.package", "count_lines_of_code_in_modules", [], {}).then((result) => {
            this.state.quality_monitoring = result.result
        });
    }

    // module lines toggle function
    async displayAuthorModules(author) {
        if (this.state.selectedAuthor === author) {
            this.state.selectedAuthor = null;
        } else {
            this.state.selectedAuthor = author;
        }
    }

    // fields and apps overview
    async countFields() {
        this.orm.call("module.quality.package", "fields_and_apps_overview", [], {}).then((result) => {
            this.state.field = result
        });
    }

    //  report function for violations
    async getAllModulesAndIcon() {
        try {
            const result = await this.orm.call("module.quality.package", "get_module_and_icons", [], {});
            this.state.all_modules = result;
        } catch (error) {
            console.error("Error fetching PEP standard template:", error);
        }
    }

    // module violation function
    async checkModuleViolations(name) {
        try {
            if (!this.state.expanded_accordian) {
                this.state.loading_accordian = true;
                this.state.expanded_accordian = true;
                this.state.selectedModule = name;
                const result = await this.orm.call("module.quality.package", "check_violations", [name], {});
                this.state.module_selected = result;
                this.state.loading_accordian = false;
            } else {
                this.state.expanded_accordian = false;
            }
        } catch (error) {
            console.error("Error fetching violations:", error);
        }
    }

    displayViolations(name) {
        if (this.state.selectedModule === name) {
            this.state.selectedModule = null;
            this.state.module_selected = null;
        } else {
            this.checkModuleViolations(name);
        }
    }

    async renderOverviewChart() {
        const canvas = this.overview?.el;
        if (!canvas) {
            return;
        }

        const ctx = canvas.getContext("2d");

        if (this.gaugeChart) {
            this.gaugeChart.destroy();
        }

        if (this.state?.field !== undefined && this.state?.field !== null) {
            const gaugeValue = this.state.field.critical_overview.overall_percentage['value']; // Example: 80
            const totalAngle = 180; // Half-circle
            const pointerAngle = (gaugeValue / 100) * totalAngle - 90;

            // Determine dot color based on value
            let dotColor = "#f36c21"; // Default Red
            if (gaugeValue >= 75) dotColor = "#EA973D"; // Orange
            else if (gaugeValue >= 50) dotColor = "#f8d31d"; // Yellow

            // Draw the gauge chart
            this.gaugeChart = new Chart(ctx, {
                type: "doughnut",
                data: {
                    datasets: [
                        {
                            data: [40, 40, 20, 20], // Segment values
                            backgroundColor: ["#f36c21", "#f8d31d", "#EA973D", "#75C57F"],
                            borderWidth: 0,
                            borderRadius: 5,
                        },
                    ],
                },
                options: {
                    responsive: false,
                    maintainAspectRatio: false,
                    rotation: -90,
                    circumference: 180,
                    cutout: "90%",
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: false },
                    },
                },
            });

            // Remove any existing dots (in case of re-render)
            const oldDot = canvas.parentElement.querySelector(".gauge-dot");
            if (oldDot) oldDot.remove();

            // Create the dot indicator
            const dot = document.createElement("div");
            dot.className = "gauge-dot"; // for easy removal later
            dot.style.position = "absolute";
            dot.style.width = "14px";
            dot.style.height = "14px";
            dot.style.background = dotColor;
            dot.style.borderRadius = "50%";
            dot.style.border = "3px solid white";
            dot.style.boxShadow = "0px 0px 5px rgba(0,0,0,0.2)";
            dot.style.transformOrigin = "center";

            const outerRadius = 85;
            const innerRadius = 55;
            const dotRadius = (outerRadius + innerRadius) / 2;
            const radians = pointerAngle * (Math.PI / 180);

            const xOffset = dotRadius * Math.cos(radians);
            const yOffset = dotRadius * Math.sin(radians);

            dot.style.left = `calc(50% + ${xOffset}px - 7px)`;
            dot.style.top = `calc(55% - ${yOffset}px - 7px)`;

        } else {
            if (this.overviewText?.el) {
                this.overviewText.el.innerText = 'Loading...';
            }
        }
    }
}

ModuleQuality.template = "odoo_health_report.module_quality_template"
registry.category('actions').add('module_quality_tag', ModuleQuality);
