"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { VerdictBadge } from "@/components/Badges";
import { StateMessage } from "@/components/StateMessage";
import { api, ApiError, errorMessage } from "@/lib/api";
import {
  allergenLabel,
  dietLabel,
  hasConstraints,
  toRequestProfile,
} from "@/lib/diet";
import { useHydrated, useSavedProfile } from "@/lib/profileStore";
import { refreshSession, useSession } from "@/lib/session";
import type {
  AssistantCard,
  AssistantMessage,
  Profile,
  User,
} from "@/lib/types";
import { useAsync } from "@/lib/useAsync";

// Matches ASSISTANT_MAX_MESSAGE_CHARS on the server (500 unless changed there).
// The server is the real limit: it answers 422 for a longer message.
const MAX_CHARS = 500;

const messageTime = new Intl.DateTimeFormat(undefined, {
  dateStyle: "short",
  timeStyle: "short",
});

async function withSession<T>(request: Promise<T>): Promise<T> {
  try {
    return await request;
  } catch (error) {
    // Check the shared login state again if the session expired.
    if (error instanceof ApiError && error.status === 401)
      void refreshSession();
    throw error;
  }
}

// What the saved profile means, in words, for the line above the chat box.
function describeProfile(profile: Profile): string[] {
  const parts = [
    ...profile.diets.map(dietLabel),
    ...profile.avoid.map((key) => `No ${allergenLabel(key).toLowerCase()}`),
  ];
  if (profile.min_protein_g != null)
    parts.push(`at least ${profile.min_protein_g} g protein`);
  if (profile.max_calories != null)
    parts.push(`up to ${profile.max_calories} calories`);
  if (profile.max_sodium_mg != null)
    parts.push(`up to ${profile.max_sodium_mg} mg sodium`);
  return parts;
}

function sendError(failure: unknown): string {
  if (failure instanceof ApiError && failure.status === 429) {
    const wait = failure.retryAfterSeconds;
    return wait
      ? `You’re asking too fast. Try again in ${wait} seconds.`
      : "You’re asking too fast. Try again in a moment.";
  }
  return errorMessage(failure);
}

export function AssistantPanel() {
  const session = useSession();
  if (session.status === "loading") {
    return <StateMessage kind="loading">Checking your account…</StateMessage>;
  }
  if (session.status === "unknown") {
    return (
      <StateMessage kind="error" onRetry={() => void refreshSession()}>
        Can’t reach the PackPlate server right now.
      </StateMessage>
    );
  }
  if (session.status === "signed_out") {
    return (
      <StateMessage kind="empty">
        <Link href="/login">Log in</Link> or{" "}
        <Link href="/signup">create an account</Link> to use the Dining
        Assistant.
      </StateMessage>
    );
  }
  // Start fresh when someone switches accounts so their chats stay separate.
  return <AssistantWorkspace key={session.user.id} user={session.user} />;
}

// The result cards (menu items) a reply came with: what it is, its numbers, and
// whether it fits. A missing number is left out, never shown as zero.
function Cards({ cards }: { cards: AssistantCard[] }) {
  if (cards.length === 0) return null;
  return (
    <ul className="assistant-cards" aria-label="Menu items from this answer">
      {cards.map((card) => {
        const numbers = [
          card.calories != null ? `${card.calories} cal` : null,
          card.protein_g != null ? `${card.protein_g} g protein` : null,
        ].filter(Boolean);
        return (
          <li className="assistant-card" key={`${card.meal}-${card.id}`}>
            <span>
              <span className="assistant-card-name">{card.name}</span>
              <span className="meta">
                {" "}
                · {card.meal}
                {numbers.length ? ` · ${numbers.join(", ")}` : ""}
              </span>
            </span>
            <VerdictBadge verdict={card.verdict} reasons={card.reasons} />
          </li>
        );
      })}
    </ul>
  );
}

function AssistantWorkspace({ user }: { user: User }) {
  void user; // the key above is what keeps one account's chat from showing in another's
  const profile = useSavedProfile();
  const hydrated = useHydrated();
  const history = useAsync(
    () => withSession(api.assistantMessages()),
    "assistant-history",
  );
  const locations = useAsync(() => api.locations(), "assistant-locations");

  // Messages sent in this visit, after the saved history was loaded.
  const [sent, setSent] = useState<AssistantMessage[]>([]);
  const [cleared, setCleared] = useState(false);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState<"send" | "clear" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const tempId = useRef(0);
  const log = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const followLatest = useRef(true);

  const messages = cleared ? sent : [...(history.data ?? []), ...sent];
  const latestId = messages.at(-1)?.id;

  // Scroll to new messages while you're near the bottom of the chat.
  useEffect(() => {
    if (log.current && followLatest.current) {
      log.current.scrollTop = log.current.scrollHeight;
    }
  }, [latestId]);

  // Examples that work with real data: the first location the server lists.
  const place = locations.data?.[0]?.name;
  const suggestions = [
    place ? `What's for dinner at ${place} tonight?` : null,
    place ? `Vegan options at ${place}` : null,
    "What's open right now?",
    place ? `Is ${place} busy right now?` : null,
  ].filter((text): text is string => text !== null);

  async function send(text: string) {
    const question = text.trim();
    if (!question || busy) return;
    setBusy("send");
    setError(null);
    try {
      const reply = await withSession(
        api.sendAssistantMessage(question, toRequestProfile(profile)),
      );
      const now = new Date().toISOString();
      setSent((previous) => [
        ...previous,
        {
          id: --tempId.current,
          role: "user",
          text: question,
          cards: [],
          created_at: now,
        },
        {
          id: --tempId.current,
          role: "assistant",
          text: reply.reply,
          cards: reply.cards,
          created_at: now,
        },
      ]);
      followLatest.current = true;
      // Keep the draft available until the message goes through.
      setDraft("");
    } catch (failure) {
      setError(sendError(failure));
    } finally {
      setBusy(null);
      input.current?.focus();
    }
  }

  async function clearHistory() {
    if (busy) return;
    setBusy("clear");
    setError(null);
    try {
      await withSession(api.clearAssistantMessages());
      setCleared(true);
      setSent([]);
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setBusy(null);
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void send(draft);
  }

  // Don't offer the chat until the saved history is in, so it can't repeat itself.
  if (history.loading) {
    return <StateMessage kind="loading">Loading your chat…</StateMessage>;
  }
  if (history.error) {
    return (
      <StateMessage kind="error" onRetry={history.reload}>
        {history.error}
      </StateMessage>
    );
  }

  return (
    <section className="panel stack" aria-labelledby="assistant-title">
      <div className="location-row-head">
        <h2 id="assistant-title" className="section-title">
          Your assistant
        </h2>
        {messages.length > 0 ? (
          <button
            className="btn btn-quiet btn-small"
            type="button"
            disabled={busy !== null}
            onClick={() => void clearHistory()}
          >
            {busy === "clear" ? "Clearing…" : "Clear chat"}
          </button>
        ) : null}
      </div>

      {hydrated ? (
        hasConstraints(profile) ? (
          <p className="help">
            Using your saved diet: {describeProfile(profile).join(", ")}.{" "}
            <Link href="/profile">Change</Link>
          </p>
        ) : (
          <p className="help">
            No dietary restrictions saved, so menus won’t be filtered.{" "}
            <Link href="/profile">Set your diet</Link>
          </p>
        )
      ) : null}

      {messages.length > 0 ? (
        <div
          className="chat-log assistant-log"
          role="log"
          aria-label="Conversation"
          tabIndex={0}
          ref={log}
          onScroll={(event) => {
            const { scrollHeight, scrollTop, clientHeight } =
              event.currentTarget;
            followLatest.current = scrollHeight - scrollTop - clientHeight < 32;
          }}
        >
          <ul className="stack">
            {messages.map((message) => {
              const own = message.role === "user";
              return (
                <li
                  className={
                    own ? "chat-message chat-message-own" : "chat-message"
                  }
                  key={message.id}
                >
                  <div className="chat-message-meta">
                    <strong>{own ? "You" : "Assistant"}</strong>
                    <time dateTime={message.created_at}>
                      {messageTime.format(new Date(message.created_at))}
                    </time>
                  </div>
                  <p>{message.text}</p>
                  <Cards cards={message.cards} />
                </li>
              );
            })}
          </ul>
        </div>
      ) : (
        <div className="stack">
          <p className="help">Try asking:</p>
          <ul className="assistant-suggestions">
            {suggestions.map((text) => (
              <li key={text}>
                <button
                  className="btn btn-outline btn-small"
                  type="button"
                  disabled={busy !== null}
                  onClick={() => void send(text)}
                >
                  {text}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <form className="stack" onSubmit={submit}>
        <div className="field">
          <label htmlFor="assistant-message">Ask a question</label>
          <textarea
            id="assistant-message"
            className="input chat-message-input"
            rows={2}
            maxLength={MAX_CHARS}
            value={draft}
            ref={input}
            disabled={busy !== null}
            onChange={(event) => setDraft(event.target.value)}
          />
        </div>
        <div className="button-row">
          <button
            className="btn btn-small"
            type="submit"
            disabled={!draft.trim() || busy !== null}
          >
            {busy === "send" ? "Thinking…" : "Send"}
          </button>
        </div>
      </form>
      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}

      <p className="help">
        Automated assistant. Labels can be wrong; check ingredients. Your
        messages are saved to your account, and you can clear them any time.
      </p>
    </section>
  );
}
