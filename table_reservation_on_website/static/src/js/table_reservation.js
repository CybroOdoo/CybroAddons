/** @odoo-module */
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class TableReservationFloor extends Interaction {
    static selector = ".swa_container";
    dynamicContent = {
        "#floors_rest": {
            "t-on-change": this.onFloorChange,
        },
        "#table_container_row": {
            "t-on-click": this.onTableClick,
        },
    };

    setup() {
        this.bookedTables = [];
    }

    start() {
        const floorSelect = this.el.querySelector("#floors_rest");
        if (floorSelect && floorSelect.value && floorSelect.value !== "0") {
            this.onFloorChange();
        }
    }

    async onFloorChange() {
        const floorSelect = this.el.querySelector("#floors_rest");
        const floors = floorSelect ? floorSelect.value : "0";

        const dateBookingEl = this.el.querySelector("#date_booking");
        const dateInputEl = this.el.querySelector("#date_id");
        const date = (dateBookingEl?.textContent || dateInputEl?.value || "").trim();

        const startBookingEl = this.el.querySelector("#booking_start");
        const startInputEl = this.el.querySelector("#start_id");
        const start = (startBookingEl?.textContent || startInputEl?.value || "").trim();

        const endBookingEl = this.el.querySelector("#booking_end");
        const endInputEl = this.el.querySelector("input[name='end_time']");
        const end = (endBookingEl?.textContent || endInputEl?.value || "").trim();

        const countTableEl = this.el.querySelector("#count_table");
        if (countTableEl) {
            countTableEl.textContent = "0";
        }
        const totalAmountEl = this.el.querySelector("#total_amount");
        if (totalAmountEl) {
            totalAmountEl.textContent = "0";
        }
        const amountRow = this.el.querySelector("#booking_amount_row");
        if (amountRow) {
            amountRow.style.display = "none";
        }
        const submitBtn = this.el.querySelector(".submit_button");
        if (submitBtn) {
            submitBtn.disabled = true;
        }

        this.bookedTables = [];
        const bookedElement = this.el.querySelector("#tables_input");
        if (bookedElement) {
            bookedElement.value = "";
        }

        const infoDiv = this.el.querySelector("#info");
        const tableContainerRow = this.el.querySelector("#table_container_row");

        if (!floors || floors === "0") {
            if (tableContainerRow) {
                tableContainerRow.innerHTML = "";
            }
            if (infoDiv) {
                infoDiv.style.display = "none";
            }
            return;
        }

        try {
            const data = await rpc("/restaurant/floors/tables", {
                floors_id: floors,
                date: date,
                start: start,
                end: end,
            });

            if (tableContainerRow) {
                tableContainerRow.innerHTML = "";
            }
            if (infoDiv) {
                infoDiv.style.display = "block";
            }

            if (data && tableContainerRow) {
                const keys = Object.keys(data);
                if (keys.length === 0) {
                    tableContainerRow.innerHTML = '<div class="col-12 py-3 text-muted"><em>No tables available for this floor and time slot.</em></div>';
                    return;
                }
                for (const i of keys) {
                    const table = data[i];
                    let amount = "";
                    if (table.rate && table.rate !== 0) {
                        amount = `<br/><span><i class="fa fa-money"></i></span> <span id="rate">${table.rate}</span>/Slot`;
                    }
                    const margin = keys.length > 1 ? "10px" : "15px";
                    const card = `
                        <div id="${table.id}" class="card card_table col-sm-2" style="background-color:#96ccd5;padding:12px;margin:${margin};width:220px;cursor:pointer;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.1);user-select:none;">
                            <div class="card-body p-0 text-center">
                                <b style="font-size:18px;">${table.name}</b>
                                <br/><br/>
                                <span><i class="fa fa-user-o" aria-hidden="true"></i> ${table.seats} Seats</span>
                                ${amount}
                            </div>
                        </div>
                    `;
                    tableContainerRow.insertAdjacentHTML("beforeend", card);
                }
            }
        } catch (error) {
            console.error("Error fetching restaurant tables:", error);
        }
    }

    onTableClick(ev) {
        const currentCard = ev.target.closest(".card_table");
        if (!currentCard) {
            return;
        }

        const tableId = Number(currentCard.id);
        const rateElement = currentCard.querySelector("#rate");
        const rate = rateElement ? parseFloat(rateElement.textContent) || 0 : 0;

        const countElement = this.el.querySelector("#count_table");
        const amountElement = this.el.querySelector("#total_amount");
        const bookedElement = this.el.querySelector("#tables_input");
        const submitBtn = this.el.querySelector(".submit_button");

        let currentCount = countElement ? parseInt(countElement.textContent) || 0 : 0;
        let currentAmount = amountElement ? parseFloat(amountElement.textContent) || 0 : 0;

        const isSelected = currentCard.style.backgroundColor === "green" || currentCard.style.backgroundColor === "rgb(0, 128, 0)";

        if (isSelected) {
            // Deselect
            const index = this.bookedTables.indexOf(tableId);
            if (index > -1) {
                this.bookedTables.splice(index, 1);
            }
            currentCard.style.backgroundColor = "#96ccd5";
            currentCount = Math.max(0, currentCount - 1);
            currentAmount = Math.max(0, currentAmount - rate);
        } else {
            // Select
            if (!this.bookedTables.includes(tableId)) {
                this.bookedTables.push(tableId);
            }
            currentCard.style.backgroundColor = "green";
            currentCount += 1;
            currentAmount += rate;
        }

        if (countElement) {
            countElement.textContent = currentCount;
        }
        if (amountElement) {
            amountElement.textContent = currentAmount;
        }
        const amountRow = this.el.querySelector("#booking_amount_row");
        if (amountRow) {
            amountRow.style.display = currentCount > 0 ? "" : "none";
        }
        if (bookedElement) {
            bookedElement.value = this.bookedTables.join(",");
        }
        if (submitBtn) {
            submitBtn.disabled = this.bookedTables.length === 0;
        }
    }
}

registry.category("public.interactions").add("table_reservation_on_website.table_reservation", TableReservationFloor);
