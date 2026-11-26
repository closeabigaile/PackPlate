# M0 — Project 3 risk-killer eval

**Status (2026-11-19):** local and hosted evaluations completed. Both new
targets met. The [successful GitHub run](https://github.com/closeabigaile/PackPlate/actions/runs/44661125326)
also reproduced both inherited M0 loops. [Issue #8](https://github.com/closeabigaile/PackPlate/issues/8)
is being maintained by Abigail.

This is the new M0 for Project 3's accounts and private collaboration.
The inherited [Project 2 M0](m0-eval.md) remains separate. Project 3 requires
both its numbers and a new claim for our additions:
[assignment](https://github.com/txt/se26f/blob/main/docs/submit/3/proj3.md#scope),
[M0 rules](https://github.com/txt/se26f/blob/main/docs/submit/2/proj2.md#m0-the-risk-killer-eval-a-required-milestone).

## The risk

PackPlate helps students find somewhere they can eat together. Our accounts
and chat add a way to coordinate that meal inside the application. This
depends on students being able to use their own conversations reliably,
while people without permission cannot read or write them.

If members cannot join, exchange messages, or return to a conversation, the
collaboration workflow is unusable. If outsiders or invalid sessions can
access it, its privacy promise is broken. Either finding could stop us from
shipping that part of Project 3 until we fix it or narrow its scope.

**The evaluation is the risk-killer.** It cheaply tests this assumption with
synthetic users. It does not establish that students want chat or make
dining decisions faster.

## Hypothesis

> Across a fixed, reproducible set of simulated multi-user journeys,
> PackPlate successfully completes 100% of specified authorized account-and-chat
> workflows and permits zero unauthorized reads or writes of private chat
> messages.

One hypothesis with two conditions; both must hold.

| Condition | Metric | Threshold | Initial baseline |
|---|---|---|---|
| Reliable collaboration | Completed authorized journeys divided by all specified authorized journeys | 100% | 6 of 6 at application revision `e0f913d` |
| Private collaboration | Forbidden message reads or writes that are accepted, reveal private messages, or change stored messages | 0 | 0 of 21 attempts at the same revision |

The baseline is the initial Project 3 account/chat implementation,
[`e0f913d119b48b540b86abc6d48941a6a4939cbf`](https://github.com/closeabigaile/PackPlate/commit/e0f913d119b48b540b86abc6d48941a6a4939cbf).
The application code was not changed to obtain these results. The inherited
application had no accounts or chat, so it cannot provide an account benchmark.
We are measuring acceptance of our extension, not claiming improvement over
an inherited account system.

The permission rules below were confirmed, and the scenario counts fixed,
before scoring. The independent permission matrix provides the expected answers,
not a measured baseline.

## The instrument

Three files stay together in [eval_project3/](../eval_project3/):

- [scenarios.json](../eval_project3/scenarios.json): the fixed cases and expected outcomes.
- [m0.py](../eval_project3/m0.py): the runnable evaluator and its faulty controls.
- [results.json](../eval_project3/results.json): the baseline counts, per-case outcomes, and source hashes.

**Simulated users.** Each case starts with fictional Alice, Bob, and Charlie
registering through the actual API and using separate session cookies.
Rooms, invitations, and messages are also created through the API. A new,
temporary schema in a dedicated local PostgreSQL database holds this data
and is removed afterward. No shared team database or real users are used.

**Six authorized journeys:** a conversation with logout and sign-in; two
separate groups; leaving a three-person group; leaving a two-person group;
deleting an account from a three-person group; and deleting an account from
a two-person group. A journey passes only if every required step returns the
expected identity, membership, history, and stored messages.

**Twenty-one denied attempts:** read and write attempts for each of nine
conditions (outsider, unaccepted invitation, declined invitation, former
member, missing session, invalid session, expired session, logged-out session,
and deleted account), plus writes to pending and inactive rooms and an
attempt to supply another user's sender ID.

| Situation | Expected message access |
|---|---|
| Joined member of an active room with a valid session | Read and write using their own sender identity |
| Creator of a pending room | Read history; no writes before activation |
| Invitee who has not joined, outsider, or former member | No reads or writes |
| Remaining member of an inactive room | Read retained history; no new messages |
| Missing, invalid, expired, logged-out, or deleted-account session | No protected reads or writes |
| Member supplying another account's sender ID | Request rejected; no message saved |

The evaluator compares actual responses with the frozen rules. It also reads
stored message rows independently: a refused response cannot hide a saved
message or leaked content. Skipped or unexecuted cases cannot count as a pass.

**Faulty controls.** An isolated version that blocks a legitimate member
must fail its journey. Another that skips membership checks must expose the
outsider's read and write. Both controls were detected. These temporary
patches are restored and do not change application files.

**Reproducibility.** Results identify the application, evaluator, and scenario
content with SHA-256 hashes. CI compares metrics, individual outcomes, controls,
and evaluator/scenario identity. It prints the current application hash but
does not require it to match the initial hash: unrelated teammate edits
should not fail M0 when the same behaviors still reproduce.

## Reproduce

Use Python 3.12 and the existing backend dependencies. From `proj_2/` in
your Python environment:

```bash
python -m pip install -r backend/requirements.txt
```

Start a disposable database, for example with Docker:

```bash
docker run --detach --rm --name packplate-m0-project3 \
  --env POSTGRES_USER=packplate --env POSTGRES_PASSWORD=packplate \
  --env POSTGRES_DB=packplate_m0_project3 \
  --publish 127.0.0.1:55437:5432 postgres:16
docker exec packplate-m0-project3 pg_isready -U packplate
```

Once it reports that connections are accepted:

```bash
export M0_DATABASE_URL=postgresql://packplate:packplate@127.0.0.1:55437/packplate_m0_project3
python eval_project3/m0.py --check
```

The script accepts only a local database named `packplate_m0_project3`.
It refuses a missing URL or a different database, and creates and removes
only its own temporary schema. An API server does not need to be running.

Without `--check`, it records a new `results.json`. Preserve the baseline
in Git and review the finding before recording a later loop. A missed target
is printed and recorded; a reproduction check can pass while that target is
missed. Missing cases, failed controls, crashes, or changed outcomes fail
the reproduction check.

Stop the disposable container afterward:

```bash
docker stop packplate-m0-project3
```

The separate [Project 3 workflow](../../.github/workflows/m0_project3.yml)
runs this check using PostgreSQL 16. It is the only M0 evaluation in routine
Project 3 CI. Both inherited M0 loops remain available manually as
historical evidence; the earlier runs recorded below also reproduced them.

## Result

Local measurements on 2026-11-19, using the existing Python 3.12 environment
and disposable PostgreSQL 16:

| Measure | Result | Target |
|---|---|---|
| Authorized journeys completed | **6/6 (100%)** | Met |
| Unauthorized reads or writes | **0/21** | Met |
| Denied attempts actually executed | **21/21** | All required |
| Blocked legitimate member detected | **Yes** | Required |
| Allowed outsider read and write detected | **Both detected** | Required |

Both inherited runs also reproduced their committed results:

| Inherited eval | Safety | Simulated groups answered |
|---|---|---|
| Loop 1 | 6 confirmed false fits in 7,926 checked; target missed | 1,000/1,000 (100%) |
| Loop 2 | 0 misses in 50 sampled answers, including 5 unclear | 902/1,000 (90.2%) |

**Review recommendation:** persevere with the current account/chat scope,
while retaining this benchmark as the other features are added. This is a
recommendation; the team's decision has not been recorded in Issue #8.

## Limits to state in the results

- The automated cases are fixed synthetic scenarios, not a representative sample of students.
- Passing does not prove all possible access paths, concurrent requests, or
  deployment configurations are safe.
- This API evaluation does not establish browser UI behavior, adoption,
  usability, performance, or comprehensive password security.
- Privacy here concerns chat messages. Username lookup and the opt-in Open to
  Chat directory are intentional features.
- Deleted users' messages remain available to permitted members with a null
  sender ID. Deletion is not a promise to erase those shared messages.
- These results do not replace the inherited dietary safety evaluation.

## If it fails

Report the numbers and failed scenario IDs in Issue #8. Hold a spiral review
and record the team's choice: persevere, re-plan, or descope. Fix access or
workflow failures, or withhold collaboration until its requirements can be
met. Retain the original evidence and rerun the same scenarios after a fix;
do not silently remove failing cases or lower thresholds.

## Bonus: real evidence

**Trial date:** November 18, 2026. **Tested branch:** `Abigail/M0_Eval`
(reported as the M0 branch).

Abigail reported a trial with three friends-and-family participants: a
friend, her brother, and her sister. The results below are the reported
observations, not an additional run of the automated evaluator.

**P** = completed without help; **H** = completed with help; **N/A** = not
assigned to that participant.

| Task | P1 | P2 | P3 |
|---|---|---|---|
| Create an account | P | P | P |
| Create a room and invite the others | P | N/A | N/A |
| Find and accept the invitation | N/A | P | P |
| Send a pretend dining message | P | P | P |
| Read another member's message | P | P | P |
| Log out and sign back in | H | P | P |
| Return to the room and see earlier messages | P | P | P |

- **3/3 participants** completed all their assigned tasks.
- **2/3** completed all assigned tasks without help.
- **1/3** completed them with slight help on locating the logout.
- No assigned tasks were marked as failed.

**Observed difficulty:** P1 took a while to find the logout button and needed
help locating it. This is a finding about locating the button; it does not establish a login or session failure. A suggested follow-up is to review how logout is presented and
retest that task.

This small friends-and-family sample adds evidence about the observed user
workflow. It does not represent the student population or independently
verify protection against unauthorized access. Keep these results separate
from the automated **6/6 journeys and 0/21 unauthorized accesses**; no
automated thresholds or results were changed for the pilot.

## Checklist

- [x] Risk, claim, metrics, thresholds, and baseline defined
- [x] Permission rules confirmed and case counts fixed before scoring
- [x] Synthetic instrument, independent outcome checks, and faulty controls run
- [x] Initial application baseline measured without changing feature code
- [x] Both inherited M0 loops reproduced
- [x] Separate Project 3 CI workflow added
- [x] Hosted GitHub CI run completed
- [x] Issue #8 description and team review decision completed

## Prepared update for Issue #8

The following summary is ready to add to the issue once the team confirms
the review decision:

> M0 evaluates whether Project 3's accounts support reliable, private
> collaboration. The claim requires 100% completion of six fixed authorized
> journeys and zero unauthorized reads or writes in 21 fixed attempts.
> Permission rules and case counts were set locally before scoring; the
> GitHub issue description was not completed before that run.
>
> On the initial application revision e0f913d119b48b540b86abc6d48941a6a4939cbf,
> all 6 journeys completed and 0 of 21 attempts gained unauthorized access.
> The evaluator caught a deliberately blocked member and deliberately
> allowed outsider reads and writes. Both inherited M0 runs reproduced their
> existing numbers, including loop 1's safety miss.
>
> Evidence and reproduction: proj_2/docs/m0-eval-project3.md and
> proj_2/eval_project3/. The separate CI workflow is
> .github/workflows/m0_project3.yml. These synthetic API results do not
> establish real-user usability or universal security.
>
> Hosted CI passed: https://github.com/closeabigaile/PackPlate/actions/runs/44661125326
>
> Recommended decision: persevere with the current account/chat scope and
> keep running the benchmark. Team decision: pending confirmation in the issue.
