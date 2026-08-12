/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

export class NoteMaker extends Component {
    /**
     * Component to manage notes.
     */
    static template = 'personal_organiser.notemaker';

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            newNote: '',
            note_title: '',
            notes: [],
        });
        this.fetchUserNotes();
    }

    /**
     * Fetches all notes for the current user and updates the state.
     */
    async fetchUserNotes() {
        try {
            this.state.notes = await this.orm.searchRead("note.maker",
                [["user_id", "=", user.userId]],
                ['id', 'note_title', 'note']
            );
        } catch (error) {
            console.error("Error fetching notes:", error);
        }
    }

    /**
     * Adds a new note for the user.
     */
    async addNote() {
        if (!this.state.newNote || !this.state.note_title) {
            return;
        }

        try {
            const [noteId] = await this.orm.create("note.maker", [{
                user_id: user.userId,
                note: this.state.newNote,
                note_title: this.state.note_title,
            }]);

            const newNote = {
                id: noteId,
                note_title: this.state.note_title,
                note: this.state.newNote,
            };

            this.state.notes.push(newNote);

            // Clear the input fields
            this.state.newNote = '';
            this.state.note_title = '';
        } catch (error) {
            console.error("Error adding note:", error);
        }
    }

    /**
     * Deletes a note by its ID.
     */
    async deleteNote(note) {
        if (note.id) {
            try {
                await this.orm.unlink("note.maker", [note.id]);
                this.state.notes = this.state.notes.filter(n => n.id !== note.id);
            } catch (error) {
                console.error("Error deleting note:", error);
            }
        } else {
            console.error("Note ID is missing:", note);
        }
    }

    /**
     * Toggles the edit mode for a note.
     */
    editNote(note) {
        note.isEditing = !note.isEditing;
    }

    /**
     * Saves changes made to a note.
     */
    async saveNote(note) {
        if (note.id) {
            try {
                await this.orm.write("note.maker", [note.id], {
                    note_title: note.note_title,
                    note: note.note,
                });
                note.isEditing = false;
            } catch (error) {
                console.error("Error saving note:", error);
            }
        } else {
            console.error("Note ID is missing:", note);
        }
    }
}
