# Third-party libraries

Every library, tool, and asset PackPlate uses, with its license. The licenses
were read from each package's own metadata (the installed Python packages, and
the npm lockfile `proj_2/frontend/package-lock.json`), not assumed. Versions
are the ones installed when this list was made (2026-10-19). Python
requirements files don't pin most versions, so a fresh install may get newer
ones.

PackPlate itself is MIT licensed (see [LICENSE.md](LICENSE.md)).

## Python: direct dependencies

From `proj_2/backend/requirements.txt`, `proj_2/ingestion/requirements.txt`,
and `proj_2/requirements-dev.txt`.

| Package | Version | Used for | License |
|---|---|---|---|
| fastapi | 0.144.0 | The web API | MIT |
| uvicorn[standard] | 0.54.0 | Runs the API server | BSD-3-Clause |
| sqlalchemy | 2.1.5 | Database models and queries | MIT |
| alembic | 1.20.0 | Database migrations | MIT |
| psycopg[binary] | 3.3.6 | PostgreSQL driver | LGPL-3.0-only |
| tzdata | 2026.5 | Time zone data (campus time) | Apache-2.0 |
| httpx2 | 2.13.1 | The scraper's HTTP client | BSD-3-Clause |
| beautifulsoup4 | 4.15.0 | Parsing the scraped HTML | MIT |
| lxml | 6.1.3 | HTML parser used by BeautifulSoup | BSD-3-Clause |
| pytest | 9.1.1 | Tests | MIT |
| pytest-cov | 7.1.0 | Test coverage | MIT |
| ruff | 0.17.1 | Python linter (dev only) | MIT |
| black | 26.10.1 | Python formatter (dev only) | MIT |
| pre-commit | 4.7.0 | Commit hooks (dev only) | MIT |

## Python: installed with the packages above

| Package | Version | License |
|---|---|---|
| annotated-doc | 0.0.5 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.15.1 | MIT |
| cfgv | 3.5.0 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| colorama | 0.4.6 | BSD |
| coverage | 7.16.2 | Apache-2.0 |
| distlib | 0.4.4 | PSF-2.0 |
| filelock | 4.2.2 | MIT |
| h11 | 0.16.0 | MIT |
| httpcore2 | 2.13.1 | BSD-3-Clause |
| httptools | 0.9.0 | MIT |
| identify | 2.6.20 | MIT |
| idna | 3.20 | BSD-3-Clause |
| iniconfig | 2.3.1 | MIT |
| Mako | 1.4.3 | MIT |
| MarkupSafe | 3.0.4 | BSD-3-Clause |
| mypy_extensions | 1.1.0 | MIT |
| nodeenv | 1.11.0 | BSD |
| opentelemetry-api | 1.45.1 | Apache-2.0 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pathspec | 1.1.1 | MPL-2.0 |
| platformdirs | 4.13.4 | MIT |
| pluggy | 1.7.0 | MIT |
| psycopg-binary | 3.3.6 | LGPL-3.0-only |
| pydantic | 2.14.1 | MIT |
| pydantic_core | 2.50.1 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| python-discovery | 1.6.3 | MIT |
| python-dotenv | 1.2.4 | BSD-3-Clause |
| pytokens | 0.4.1 | MIT |
| PyYAML | 6.0.3 | MIT |
| soupsieve | 3.0.3 | MIT |
| starlette | 1.8.0 | BSD-3-Clause |
| truststore | 0.10.5 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| typing-inspection | 0.4.4 | MIT |
| uvloop | 0.23.0 | MIT OR Apache-2.0 (Linux and macOS only, e.g. in Docker and CI) |
| virtualenv | 21.14.11 | MIT |
| watchfiles | 1.3.0 | MIT |
| websockets | 17.2 | BSD-3-Clause |

## Website (npm): direct dependencies

From `proj_2/frontend/package.json`.

| Package | Version | Used for | License |
|---|---|---|---|
| next | 16.3.8 | The website framework | MIT |
| react | 19.2.8 | UI library | MIT |
| react-dom | 19.2.8 | UI library (browser) | MIT |
| typescript | 5.9.3 | Type checking (dev only) | Apache-2.0 |
| eslint | 9.39.5 | Linter (dev only) | MIT |
| eslint-config-next | 16.3.8 | Next.js lint rules (dev only) | MIT |
| eslint-config-prettier | 10.1.8 | Keeps ESLint and Prettier from clashing (dev only) | MIT |
| prettier | 3.9.10 | Formatter (dev only) | MIT |
| @types/node | 20.19.43 | Type definitions (dev only) | MIT |
| @types/react | 19.3.0 | Type definitions (dev only) | MIT |
| @types/react-dom | 19.3.0 | Type definitions (dev only) | MIT |

## Website (npm): everything installed

The lockfile lists **405 packages** in total, all installed by the 11 above.
By license:

| License | Packages |
|---|---|
| MIT | 326 |
| Apache-2.0 | 34 |
| ISC | 16 |
| LGPL-3.0-or-later | 10 |
| BSD-2-Clause | 7 |
| Apache-2.0 AND LGPL-3.0-or-later | 3 |
| BSD-3-Clause | 2 |
| Apache-2.0 AND LGPL-3.0-or-later AND MIT | 1 |
| BlueOak-1.0.0, Python-2.0, MPL-2.0, CC-BY-4.0, CC0-1.0, 0BSD | 1 each |

The LGPL entries are all `@img/sharp-*` packages: optional, platform-specific
image-processing binaries that Next.js can use. Only the one for your platform
is installed. The other non-MIT ones are `caniuse-lite` (CC-BY-4.0), `tslib`
(0BSD), `axe-core` (MPL-2.0, dev), `argparse` (Python-2.0, dev),
`language-subtag-registry` (CC0-1.0, dev), and one copy of `minimatch`
(BlueOak-1.0.0, dev).

To see every package and its license:

```bash
cd proj_2/frontend
node -e "const l=require('./package-lock.json');for(const[k,v]of Object.entries(l.packages))if(k)console.log(k.replace('node_modules/',''),v.version,v.license)"
```

## Fonts

| Asset | Used for | License |
|---|---|---|
| Geist and Geist Mono (via `next/font/google`) | The website's fonts | SIL Open Font License 1.1 |

## Tools and services (not shipped with the code)

| Tool | Used for | License |
|---|---|---|
| PostgreSQL 16 (`postgres:16` Docker image) | The database | PostgreSQL License |
| Python 3.12 (`python:3.12-slim` Docker image) | Runs the API | PSF License 2.0 |
| Node.js 22 (`node:22-alpine` Docker image) | Runs the website | MIT |
| actions/checkout, actions/setup-python, actions/setup-node | CI (GitHub Actions) | MIT |
| schneegans/dynamic-badges-action | The test-count badge | MIT |
| astral-sh/ruff-pre-commit | Ruff commit hook | Apache-2.0 |
| psf/black-pre-commit-mirror | Black commit hook (it only installs Black, which is MIT; the mirror repo has no license file) | — |

## Data

Menus, nutrition labels, and hours come from NC State's NetNutrition
(`netmenu2.cbord.com`) and dining.ncsu.edu. They are NC State's data, not a
software library; NC State Dining gave the team permission to scrape them at
most once or twice a day. A trimmed copy for the M0 eval is committed in
`proj_2/eval/data/snapshot.json`.
