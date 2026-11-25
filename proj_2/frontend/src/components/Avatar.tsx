// A coloured circle with someone's initials, for telling group members apart
// at a glance. The name is always written next to it or in its label.
const COLORS = [
  "#cc0000",
  "#0f7280",
  "#741f9c",
  "#4f7a12",
  "#a35c00",
  "#2b5fb3",
  "#b3306f",
  "#3d3d42",
  "#00806a",
  "#7a4b1f",
];

export function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "?";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[words.length - 1][0]).toUpperCase();
}

export function Avatar({
  name,
  index,
  status,
}: {
  name: string;
  index: number;
  status?: "fits" | "none";
}) {
  return (
    <span
      className={status ? `avatar avatar-${status}` : "avatar"}
      style={{ background: COLORS[index % COLORS.length] }}
      aria-hidden="true"
    >
      {initials(name)}
      {status ? (
        <span className="avatar-badge">{status === "fits" ? "✓" : "✕"}</span>
      ) : null}
    </span>
  );
}
