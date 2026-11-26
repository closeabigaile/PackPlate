"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useSession } from "@/lib/session";
import { Icon } from "./Icon";

// The links people use most stay in the bar; the rest sit under "More" on wide
// screens. On phones the menu button shows every link in one list.
const PRIMARY = [
  { href: "/locations", label: "What’s open" },
  { href: "/menus", label: "Menus" },
  { href: "/compare", label: "Compare" },
  { href: "/group", label: "Eat as a group" },
  { href: "/chat", label: "Group chat" },
  { href: "/assistant", label: "Assistant" },
];

const MORE = [
  { href: "/busy", label: "How busy" },
  { href: "/profile", label: "My diet" },
  { href: "/", label: "About PackPlate" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);
  const session = useSession();
  // Nothing while loading or offline, so the link doesn't flicker or lie.
  const account =
    session.status === "signed_in"
      ? { href: "/account", label: session.user.username }
      : session.status === "signed_out"
        ? { href: "/login", label: "Log in" }
        : null;

  // Close "More" on a click outside it or on Escape.
  useEffect(() => {
    if (!moreOpen) return;
    function onPointer(event: PointerEvent) {
      if (!moreRef.current?.contains(event.target as Node)) setMoreOpen(false);
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setMoreOpen(false);
    }
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [moreOpen]);

  function close() {
    setOpen(false);
    setMoreOpen(false);
  }

  const moreActive = MORE.some((link) => link.href === pathname);

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Link href="/home" className="brand" onClick={close}>
          <span className="brand-mark" aria-hidden="true">
            <Icon name="utensils" size={18} />
          </span>
          <span>
            Pack<span className="brand-accent">Plate</span>
          </span>
        </Link>

        <button
          type="button"
          className="nav-toggle"
          aria-expanded={open}
          aria-controls="site-nav"
          onClick={() => setOpen((value) => !value)}
        >
          <Icon name="menu" size={18} /> Menu
        </button>

        <nav
          id="site-nav"
          aria-label="Main"
          className={open ? "nav nav-open" : "nav"}
        >
          {PRIMARY.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              aria-current={pathname === link.href ? "page" : undefined}
              onClick={close}
            >
              {link.label}
            </Link>
          ))}

          {/* Phones: the "More" links are listed like the others. */}
          {MORE.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="nav-phone-only"
              aria-current={pathname === link.href ? "page" : undefined}
              onClick={close}
            >
              {link.label}
            </Link>
          ))}

          <div className="nav-more" ref={moreRef}>
            <button
              type="button"
              className={moreActive ? "nav-more-btn is-active" : "nav-more-btn"}
              aria-expanded={moreOpen}
              aria-controls="nav-more-list"
              onClick={() => setMoreOpen((value) => !value)}
            >
              More <Icon name="chevron" size={16} className="chevron" />
            </button>
            {moreOpen ? (
              <ul id="nav-more-list" className="nav-more-list">
                {MORE.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      aria-current={pathname === link.href ? "page" : undefined}
                      onClick={close}
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>

          {account ? (
            <Link
              href={account.href}
              className="nav-account"
              aria-current={pathname === account.href ? "page" : undefined}
              onClick={close}
            >
              {session.status === "signed_in" ? (
                <Icon name="user" size={16} />
              ) : null}
              {account.label}
            </Link>
          ) : null}
        </nav>
      </div>
    </header>
  );
}
