/** @odoo-module **/
import { Component, onWillStart, useState, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { DashboardCardButtons } from "./dashboard_card_buttons";

export class DashboardTodo extends Component {
    setup() {
        this.orm = useService("orm");

        this.state = useState({
            card: this.props.card,
            todos: [],
            draggedTodo: null,
        });

        onWillStart(async () => {
            if (this.props.todos && this.props.todos.length) {
                this.state.todos = this.props.todos;
            } else if (this.props.card.todo_ids?.length) {
                this.state.todos = await this.orm.searchRead(
                    "dashboard.todo",
                    [["id", "in", this.props.card.todo_ids]],
                    ["id", "name", "status", "is_done"]
                );
            }
        });

        /* Bind methods */
        this.toggleTodo = this.toggleTodo.bind(this);
        this.onDragStart = this.onDragStart.bind(this);
        this.allowDrop = this.allowDrop.bind(this);
        this.onDrop = this.onDrop.bind(this);

        // React to prop changes (for preview)
        onWillUpdateProps(async (nextProps) => {
            this.state.card = nextProps.card;
            if (nextProps.todos) {
                this.state.todos = nextProps.todos;
            } else if (nextProps.card && nextProps.card.todo_ids) {
                this.state.todos = await this.orm.searchRead(
                    "dashboard.todo",
                    [["id", "in", nextProps.card.todo_ids]],
                    ["id", "name", "status", "is_done"]
                );
            }
        });
    }

    async toggleTodo(todo) {
        if (todo.status !== "complete") {
            todo._prev_status = todo.status;
            todo.status = "complete";
            todo.is_done = true;
        } else {
            todo.status = todo._prev_status || "low";
            todo.is_done = false;
        }

        await this.orm.write("dashboard.todo", [todo.id], {
            status: todo.status,
            is_done: todo.is_done,
        });
    }

    get sortedTodos() {
        const order = {
            high: 4,
            medium: 3,
            low: 2,
            ongoing: 1,
            complete: 0,
        };
        return [...this.state.todos].sort(
            (a, b) => order[b.status] - order[a.status]
        );
    }

    get progress() {
        if (!this.state.todos.length) return 0;
        const done = this.state.todos.filter(t => t.status === "complete").length;
        return Math.round((done / this.state.todos.length) * 100);
    }

    get todosByStatus() {
        return {
            todo: this.state.todos.filter(t =>
                ["high", "medium", "low"].includes(t.status)
            ),
            ongoing: this.state.todos.filter(t => t.status === "ongoing"),
            complete: this.state.todos.filter(t => t.status === "complete"),
        };
    }

    onDragStart(todo) {
        this.state.draggedTodo = todo;
    }

    allowDrop(ev) {
        ev.preventDefault();
    }

    async onDrop(targetStatus) {
        const todo = this.state.draggedTodo;
        if (!todo) return;

        if (targetStatus === "todo") {
            todo.status = todo._prev_status || "low";
            todo.is_done = false;
        }
        if (targetStatus === "ongoing") {
            todo.status = "ongoing";
            todo.is_done = false;
        }
        if (targetStatus === "complete") {
            todo.status = "complete";
            todo.is_done = true;
        }

        await this.orm.write("dashboard.todo", [todo.id], {
            status: todo.status,
            is_done: todo.is_done,
        });

        this.state.draggedTodo = null;
    }
}

DashboardTodo.template = "DashboardTodoTemplate";
DashboardTodo.components = { DashboardCardButtons };


