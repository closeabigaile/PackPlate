"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { api, errorMessage } from "@/lib/api";
import {
  emptyProfile,
  hasConstraints,
  MAX_PROFILES,
  toRequestProfile,
  validateProfile,
} from "@/lib/diet";
import { formatTime } from "@/lib/format";
import { useHydrated, useSavedProfile } from "@/lib/profileStore";
import type { GroupLocation, Profile } from "@/lib/types";
import { StatusPill } from "./Badges";
import { ProfileFields } from "./ProfileFields";
import { StateMessage } from "./StateMessage";

interface Member {
  id: number;
  profile: Profile;
}

type Search =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "done"; results: GroupLocation[]; labels: string[] };

function labelFor(profile: Profile, index: number): string {
  return profile.name?.trim() || `Person ${index + 1}`;
}

function ResultCard({ location, labels }: { location: GroupLocation; labels: string[] }) {
  const when =
    location.is_open === true && location.closes_at
      ? `Closes at ${formatTime(location.closes_at)}`
      : location.is_open === false
        ? location.opens_next_at
          ? `Opens again at ${formatTime(location.opens_next_at)}`
          : "Not open again today"
        : null;

  return (
    <li
      className={`panel result-card ${location.everyone_fits ? "result-everyone" : "result-left-out"}`}
    >
      <div className="location-row-head">
        <span className="location-name">{location.name}</span>
        <StatusPill isOpen={location.is_open} />
      </div>
      {when ? <p className="meta">{when}</p> : null}

      {location.items_checked === 0 ? (
        <p className="banner banner-warn">
          No menu is loaded for today, so nobody can be matched here.
        </p>
      ) : (
        <ul className="count-list">
          {location.profiles.map((counts, index) => (
            <li key={index}>
              <strong>{counts.name?.trim() || labels[index] || `Person ${index + 1}`}</strong>
              {": "}
              {counts.fits} fit · {counts.incomplete} can’t confirm · {counts.conflicts}{" "}
              don’t fit
              {counts.fits === 0 ? " — nothing here fits" : ""}
            </li>
          ))}
        </ul>
      )}

      <div className="row-links">
        <Link href={`/menus?location=${location.id}`}>View menu</Link>
      </div>
    </li>
  );
}

function GroupForm({ initial }: { initial: Profile }) {
  const [members, setMembers] = useState<Member[]>([{ id: 1, profile: initial }]);
  const [nextId, setNextId] = useState(2);
  const [search, setSearch] = useState<Search>({ status: "idle" });
  const [problem, setProblem] = useState<string | null>(null);

  function updateMember(id: number, profile: Profile) {
    setMembers((list) => list.map((m) => (m.id === id ? { ...m, profile } : m)));
  }

  function addMember() {
    setMembers((list) => [...list, { id: nextId, profile: emptyProfile() }]);
    setNextId((value) => value + 1);
  }

  function removeMember(id: number) {
    setMembers((list) => (list.length > 1 ? list.filter((m) => m.id !== id) : list));
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    for (const [index, member] of members.entries()) {
      const invalid = validateProfile(member.profile);
      if (invalid) {
        setProblem(`${labelFor(member.profile, index)}: ${invalid}`);
        return;
      }
    }
    setProblem(null);
    setSearch({ status: "loading" });
    try {
      const results = await api.filterGroup(
        members.map((m) => toRequestProfile(m.profile)),
      );
      setSearch({
        status: "done",
        results,
        labels: members.map((m, index) => labelFor(m.profile, index)),
      });
    } catch (error) {
      setSearch({ status: "error", message: errorMessage(error) });
    }
  }

  const nobodyRestricted = members.every((m) => !hasConstraints(m.profile));
  const everyone =
    search.status === "done" ? search.results.filter((r) => r.everyone_fits) : [];
  const others =
    search.status === "done" ? search.results.filter((r) => !r.everyone_fits) : [];

  return (
    <>
      <form className="members" onSubmit={onSubmit}>
        {members.map((member, index) => (
          <section
            key={member.id}
            className="panel"
            aria-label={labelFor(member.profile, index)}
          >
            <div className="member-head">
              <h2 className="section-title" style={{ marginBottom: 0 }}>
                {labelFor(member.profile, index)}
              </h2>
              {members.length > 1 ? (
                <button
                  type="button"
                  className="btn btn-quiet btn-small"
                  onClick={() => removeMember(member.id)}
                  aria-label={`Remove ${labelFor(member.profile, index)}`}
                >
                  Remove
                </button>
              ) : null}
            </div>
            <ProfileFields
              idPrefix={`member-${member.id}`}
              value={member.profile}
              onChange={(profile) => updateMember(member.id, profile)}
              showName
            />
          </section>
        ))}

        {problem ? (
          <p className="form-error" role="alert">
            {problem}
          </p>
        ) : null}

        {nobodyRestricted ? (
          <p className="banner banner-warn">
            Nobody has an allergy or preference set yet, so every location with
            a menu will match.
          </p>
        ) : null}

        <div className="button-row">
          <button
            type="button"
            className="btn btn-outline"
            onClick={addMember}
            disabled={members.length >= MAX_PROFILES}
          >
            Add a person
          </button>
          <button type="submit" className="btn" disabled={search.status === "loading"}>
            {search.status === "loading" ? "Finding a match…" : "Find a match"}
          </button>
        </div>
        {members.length >= MAX_PROFILES ? (
          <p className="help">A group can have up to {MAX_PROFILES} people.</p>
        ) : null}
      </form>

      <section aria-live="polite" aria-label="Results">
        {search.status === "error" ? (
          <StateMessage kind="error">{search.message}</StateMessage>
        ) : null}

        {search.status === "done" ? (
          search.results.length === 0 ? (
            <StateMessage kind="empty">
              No dining locations have been loaded yet.
            </StateMessage>
          ) : (
            <div className="page-body" style={{ marginTop: 0 }}>
              <div>
                <h2 className="section-title">
                  Everyone can eat here <span className="count">({everyone.length})</span>
                </h2>
                {everyone.length === 0 ? (
                  <StateMessage kind="empty">
                    No location has something for everyone today. Try removing a
                    restriction, or look at who is left out below.
                  </StateMessage>
                ) : (
                  <ul className="stack">
                    {everyone.map((location) => (
                      <ResultCard key={location.id} location={location} labels={search.labels} />
                    ))}
                  </ul>
                )}
              </div>

              {others.length > 0 ? (
                <div>
                  <h2 className="section-title">
                    Someone is left out <span className="count">({others.length})</span>
                  </h2>
                  <ul className="stack">
                    {others.map((location) => (
                      <ResultCard key={location.id} location={location} labels={search.labels} />
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          )
        ) : null}
      </section>
    </>
  );
}

export function GroupBuilder() {
  const hydrated = useHydrated();
  const saved = useSavedProfile();

  // The first person starts from your saved profile, once the browser is ready.
  if (!hydrated) return <StateMessage kind="loading">Loading…</StateMessage>;
  return <GroupForm initial={saved} />;
}
