"use client";

import { FormEvent, useEffect, useState } from "react";
import { AsyncState } from "@/components/async/AsyncState";
import { getErrorMessage } from "@/lib/api-client";
import { createNote, deleteNote, getNotes } from "@/lib/notes-service";
import { validateNoteContent } from "@/lib/validators";
import { AsyncDataState } from "@/types/api";
import { CandidateNote } from "@/types/note";

interface CandidateNotesSectionProps {
  recordId: string;
}

export function CandidateNotesSection({
  recordId,
}: CandidateNotesSectionProps) {
  const [notesState, setNotesState] = useState<AsyncDataState<CandidateNote[]>>({
    loading: true,
    error: null,
    data: null,
  });
  const [noteContent, setNoteContent] = useState("");
  const [noteFeedback, setNoteFeedback] = useState<{
    status: "idle" | "submitting" | "success" | "error";
    message: string | null;
  }>({ status: "idle", message: null });
  const [deletingNoteId, setDeletingNoteId] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadNotes() {
      try {
        setNotesState({ loading: true, error: null, data: null });
        const notes = await getNotes(recordId);

        if (active) {
          setNotesState({ loading: false, error: null, data: notes });
        }
      } catch (error) {
        if (active) {
          setNotesState({
            loading: false,
            error: getErrorMessage(error),
            data: null,
          });
        }
      }
    }

    void loadNotes();

    return () => {
      active = false;
    };
  }, [recordId]);

  async function handleCreateNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const validationMessage = validateNoteContent(noteContent);

    if (validationMessage) {
      setNoteFeedback({ status: "error", message: validationMessage });
      return;
    }

    try {
      setNoteFeedback({ status: "submitting", message: null });
      const createdNote = await createNote(recordId, { content: noteContent.trim() });

      setNotesState((currentState) => ({
        loading: false,
        error: null,
        data: [createdNote, ...(currentState.data ?? [])],
      }));
      setNoteContent("");
      setNoteFeedback({ status: "success", message: "Note added." });
    } catch (error) {
      setNoteFeedback({
        status: "error",
        message: getErrorMessage(error),
      });
    }
  }

  async function handleDeleteNote(noteId: string) {
    try {
      setDeletingNoteId(noteId);
      await deleteNote(recordId, noteId);
      setNotesState((currentState) => ({
        loading: false,
        error: null,
        data: (currentState.data ?? []).filter((note) => note.id !== noteId),
      }));
    } catch (error) {
      setNoteFeedback({
        status: "error",
        message: getErrorMessage(error),
      });
    } finally {
      setDeletingNoteId(null);
    }
  }

  return (
    <section className="section-card">
      <header>
        <h2>Notes</h2>
        <p>Track interview insights and follow-up context for this candidate.</p>
      </header>

      <form className="stack" onSubmit={handleCreateNote}>
        <div className="field">
          <label htmlFor="candidate-note">Add note</label>
          <textarea
            id="candidate-note"
            value={noteContent}
            onChange={(event) => setNoteContent(event.target.value)}
            placeholder="Add a note for the hiring team"
          />
        </div>

        {noteFeedback.status === "submitting" ? (
          <div className="feedback info" role="status" aria-live="polite">
            Saving note...
          </div>
        ) : null}

        {noteFeedback.status === "success" && noteFeedback.message ? (
          <div className="feedback info" role="status" aria-live="polite">
            {noteFeedback.message}
          </div>
        ) : null}

        {noteFeedback.status === "error" && noteFeedback.message ? (
          <div className="feedback error" role="alert">
            {noteFeedback.message}
          </div>
        ) : null}

        <div className="button-row">
          <button className="button" type="submit" disabled={noteFeedback.status === "submitting"}>
            Add note
          </button>
        </div>
      </form>

      <AsyncState
        loading={notesState.loading}
        error={notesState.error}
        loadingText="Loading notes..."
        isEmpty={(notesState.data ?? []).length === 0}
        emptyState={<div className="empty-state">No notes have been added yet.</div>}
      >
        <ul className="notes-list">
          {(notesState.data ?? []).map((note) => (
            <li className="note-item" key={note.id}>
              <div className="note-meta">
                <span>{note.author || "Team note"}</span>
                <span>{formatDate(note.createdAt)}</span>
              </div>
              <p>{note.content}</p>
              <div className="button-row">
                <button
                  className="button danger"
                  type="button"
                  disabled={deletingNoteId === note.id}
                  onClick={() => void handleDeleteNote(note.id)}
                >
                  {deletingNoteId === note.id ? "Deleting..." : "Delete note"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      </AsyncState>
    </section>
  );
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}