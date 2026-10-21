# 12 - Frontend Development from Wireframes

| | |
|---|---|
| **Author** | Savanah Hendzel |
| **Date** | 2026-10-18 |
| **Tool / model** | Claude Sonnet 5.5 |

## 1. Request

I asked it to create the frontend from the wireframes I provided. I told it this is for a group
project for school. I told it to ask me a questions if it is unsure what design direction to take. 
The constraints were to follow the design of the provided wirframes and to use the tools that we decided on.

## 2. AI proposal

I built the frontend from your wireframes as a standalone Next.js app, but I couldn’t compile, lint or run it here. The sandbox couldn’t reach the npm registry, so I couldn’t install packages or run next build. Please run npm install && npm run lint && npm run build first and fix whatever it reports.

Pages

/ and /home: Welcome page, then Home with the five cards in the 3+2 layout, using the NC State Dining card style and colors.
/login and /signup: Match the wireframe, but there’s no backend for accounts, so they send and store nothing and say so.
/locations: What’s Open Now, with open, hours-unknown and closed lists.
/menus: Dropdown per location. Open locations default to today, closed ones to the next day with a menu, and each has a date picker.
/profile: Allergies, diets and nutrition goals, saved only in the browser.
/group: Add up to 10 people, then find locations where everyone has something to eat.
/busy: Crowd levels, with report buttons that handle the 60-second throttle.

Behavior from docs/m4-web-app.md

Items the backend can’t confirm are marked “Can’t confirm” with its reasons, and “Hide items that don’t fit” never hides them.
Items with no nutrition label say allergens come from icons only.
A banner on data pages shows how old the data is and warns when it’s stale, partial or missing.

Decisions for you

No accounts. I took option 1 from the M4 doc and kept the dietary profile in localStorage.
Types are hand-written. The sandbox couldn’t reach PyPI to export the OpenAPI spec, so src/lib/types.ts mirrors the backend schemas by hand. The doc asks for generated types; npm run gen:api is set up for that once the backend is running.
Home is at /home. / is the Welcome page.
Card art is a placeholder. The cards use emoji in place of photos.

Files are in packplate-frontend.zip

## 3. Human review

The code that it gae us was reviewed. I made sure that it followed the structures of the wireframes.
I changed various design items like the emjois used, some layout options, and removed the
sign-up and login options from all screens.

Any changes to the frontend from what was provided were done manually.

## 4. Final version

What was kept and changed is what the frontend looks like now.

## 5. Verification

- [ ] Tests pass: The github tests passed.
- [ ] Ran it manually: Everyone ran the frontend manually.
