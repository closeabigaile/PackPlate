// The current time, in milliseconds. Normally just Date.now().
//
// For recording demos: NEXT_PUBLIC_DEMO_NOW=2026-11-30T12:45:00-05:00 makes the
// site's clock start at that moment when the page loads and keep ticking from
// there. Use the same moment as the API's DEMO_NOW. Unset means the real clock.
const DEMO_START = process.env.NEXT_PUBLIC_DEMO_NOW;
const OFFSET = DEMO_START ? new Date(DEMO_START).getTime() - Date.now() : 0;

export function nowMs(): number {
  return Date.now() + (Number.isNaN(OFFSET) ? 0 : OFFSET);
}
