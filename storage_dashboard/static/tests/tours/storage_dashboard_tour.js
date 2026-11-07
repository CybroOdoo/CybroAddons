import { registry } from "@web/core/registry";

registry.category("web_tour.tours").add("storage_dashboard_tour", {
    steps: () => [
        {
            content: "The system monitor shows the server information",
            trigger: ".o_storage_dashboard th:contains(Total Memory) + td:contains(GB)",
        },
        {
            content: "The database details are shown",
            trigger: ".o_storage_dashboard th:contains(Database Size) + td:contains(MB)",
        },
        {
            content: "The chart of the models is drawn",
            trigger: ".o_storage_chart canvas",
            run() {
                const chart = Chart.getChart(document.querySelector(".o_storage_chart canvas"));
                if (!chart || !chart.data.labels.length) {
                    throw new Error("The model size chart is empty");
                }
            },
        },
    ],
});
