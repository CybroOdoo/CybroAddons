/** @odoo-module **/

import { expect, test } from "@odoo/hoot";
import { ListRenderer } from "@web/views/list/list_renderer";
import "@list_view_sticky_header_and_column/js/list_view_sticky_header_and_column";

/**
 * Builds a detached DOM fixture that mimics the bits of the list view
 * markup the patch relies on: a `.o_list_table` with a header row of
 * `<th>` cells (each holding the pin icon) and a body of `.o_data_row`
 * rows with matching `<td>` cells.
 */
function makeListFixture(columnCount, rowCount) {
    const root = document.createElement("div");
    root.className = "o_list_renderer";

    const table = document.createElement("table");
    table.className = "o_list_table";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    const headerCells = [];
    for (let i = 0; i < columnCount; i++) {
        const th = document.createElement("th");
        const icon = document.createElement("i");
        icon.className = "fa fa-thumb-tack";
        th.appendChild(icon);
        headerRow.appendChild(th);
        headerCells.push(th);
    }
    thead.appendChild(headerRow);

    const tbody = document.createElement("tbody");
    const dataRows = [];
    for (let r = 0; r < rowCount; r++) {
        const row = document.createElement("tr");
        row.className = "o_data_row";
        for (let c = 0; c < columnCount; c++) {
            const td = document.createElement("td");
            row.appendChild(td);
        }
        tbody.appendChild(row);
        dataRows.push(row);
    }

    table.appendChild(thead);
    table.appendChild(tbody);
    root.appendChild(table);

    return { root, headerCells, dataRows };
}

function makeRenderer(root) {
    return { __owl__: { bdom: { parentEl: root } } };
}

function clickIcon(renderer, th) {
    const icon = th.querySelector(".fa-thumb-tack");
    let prevented = false;
    let stopped = false;
    ListRenderer.prototype._onClickIcon.call(renderer, {
        currentTarget: icon,
        preventDefault: () => (prevented = true),
        stopPropagation: () => (stopped = true),
    });
    return { prevented, stopped };
}

test("clicking a header icon pins that header and every column before it", () => {
    const { root, headerCells, dataRows } = makeListFixture(3, 2);
    const renderer = makeRenderer(root);

    const { prevented, stopped } = clickIcon(renderer, headerCells[1]);

    expect(prevented).toBe(true);
    expect(stopped).toBe(true);

    // Header 0 and 1 (up to and including the clicked one) become sticky.
    expect(headerCells[0].classList.contains("sticky-column")).toBe(true);
    expect(headerCells[1].classList.contains("sticky-column")).toBe(true);
    expect(headerCells[2].classList.contains("sticky-column")).toBe(false);

    // Only the clicked header carries the 'clicked-header' marker.
    expect(headerCells[1].classList.contains("clicked-header")).toBe(true);
    expect(headerCells[0].classList.contains("clicked-header")).toBe(false);

    // Sticky headers stay pinned to the top of the scroll area
    // (the browser normalizes the assigned '0' to '0px' on read-back).
    expect(headerCells[1].style.top).toBe("0px");

    // The first two cells of every data row become sticky, the rest don't.
    for (const row of dataRows) {
        const cells = row.querySelectorAll("td");
        expect(cells[0].classList.contains("sticky-column")).toBe(true);
        expect(cells[1].classList.contains("sticky-column")).toBe(true);
        expect(cells[2].classList.contains("sticky-column")).toBe(false);
    }
});

test("clicking a different header clears the previous sticky selection first", () => {
    const { root, headerCells, dataRows } = makeListFixture(3, 1);
    const renderer = makeRenderer(root);

    clickIcon(renderer, headerCells[2]);
    clickIcon(renderer, headerCells[0]);

    // Only column 0 should remain sticky now.
    expect(headerCells[0].classList.contains("sticky-column")).toBe(true);
    expect(headerCells[1].classList.contains("sticky-column")).toBe(false);
    expect(headerCells[2].classList.contains("sticky-column")).toBe(false);

    // The old clicked-header marker moved to the new header.
    expect(headerCells[0].classList.contains("clicked-header")).toBe(true);
    expect(headerCells[2].classList.contains("clicked-header")).toBe(false);

    const cells = dataRows[0].querySelectorAll("td");
    expect(cells[0].classList.contains("sticky-column")).toBe(true);
    expect(cells[2].classList.contains("sticky-column")).toBe(false);
});

test("clicking the same header twice keeps a single clicked-header marker", () => {
    const { root, headerCells } = makeListFixture(2, 1);
    const renderer = makeRenderer(root);

    clickIcon(renderer, headerCells[0]);
    clickIcon(renderer, headerCells[0]);

    const clicked = root.querySelectorAll(".clicked-header");
    expect(clicked.length).toBe(1);
    expect(clicked[0]).toBe(headerCells[0]);
});

test("pinning the last column leaves no un-pinned columns behind", () => {
    const { root, headerCells, dataRows } = makeListFixture(2, 1);
    const renderer = makeRenderer(root);

    clickIcon(renderer, headerCells[1]);

    expect(headerCells[0].classList.contains("sticky-column")).toBe(true);
    expect(headerCells[1].classList.contains("sticky-column")).toBe(true);

    const cells = dataRows[0].querySelectorAll("td");
    expect(cells[0].classList.contains("sticky-column")).toBe(true);
    expect(cells[1].classList.contains("sticky-column")).toBe(true);
});
