# Client Success Daily Dashboard: rebuild runbook

Internal Use Only. Attach this file, `rebuild_helpers.py` and the current `csm_dashboard.html` to a chat with Claude and paste the request from the dashboard's "Copy Claude request" button.

## Instructions to Claude: read this first

You are rebuilding the dashboard end to end. The person has asked you not to stop and ask for confirmation.

1. **Do not pause.** Do not ask "should I continue", do not offer options mid-way, do not end a turn after a partial result. Work through every dataset below in one go, then give the final file and a short summary. Only stop for a real blocker, such as a connector that is switched off, and say exactly which.
2. **Rebuild everything**, both groups below. Never report a partial rebuild as complete. In the summary, list anything you could not refresh and why.
3. **Keep chat output small, because it is the slow part.**
   - Salesforce results over about 50 KB are stored as files in `/mnt/user-data/tool_results/`. Read them with `sf_records()` in `rebuild_helpers.py`. Do not retype them.
   - To get a stored file, ask for row-level fields and add a few extra fields so the result is large. Avoid results that land inline.
   - Gainsight results come back inline, 50 rows a page. Select only the fields you need. First run a *change check* with a date filter (for example `NpsLastUpdated >= <last build date>`): an empty result means that dataset is unchanged and needs no paging.
   - Never type data you can re-derive. When you do have to type rows, compare them with the file's current values: unchanged rows must match exactly, which proves the typing.
4. **Check before replacing.** Compare each new dataset with the current one and note what changed. Keep hand corrections (see the scorecard row).
5. **Patch, don't rewrite.** Use `get_const` and `patch_const` from `rebuild_helpers.py` to replace data constants in `csm_dashboard.html`. Update the matching date constants (`SC_ASOF`, `ENG_DAY`, `NPS_ASOF`, `CT_ASOF`, `REN_ASOF`, `CR_ASOF`, `MV_ASOF`, and so on) only for data you actually re-pulled.
6. **Verify the result.** Open the file in a headless browser, confirm there are no page errors, and spot-check the Today, Account Risk, Managers View, Renewal Opportunities and Outreach tabs. Then run `python3 rebuild_helpers.py csm_dashboard.html`.
7. **Update this runbook** with anything you learned, and return it with the dashboard.

## Rules for every email the dashboard writes

These are customer-facing drafts. They must read as if the customer could see everything in them.

- **Allowed:** the customer's own figures from their scorecard and Practice Management data (for example A/R over 90 days, denial rate, cancellation rate), what came up on calls and in emails with them, information they gave Support, and a cited industry source such as HST's State of the ASC Industry Report, an HST blog post or an ASC tip, to explain why an offer (an RCM review with Synergen Health, a new product) is relevant to them.
- **Never:** Salesforce notes or stages, opportunity amounts or close dates, AE or other internal names, Gainsight objects (CTAs, health colors, health scores), NPS as a number, ticket numbers, Gong references, or internal asks such as a "stop/go". Those belong in the task steps, not in the email.
- **Tone:** specific to the customer, short, one soft ask ("would 20 minutes work?"), no pressure, no internal vocabulary. Outside examples of CSM and cross-sell emails all do the same three things: open with something specific to the customer, give one useful reason, and end with one easy next step.
- **Check:** run `python3 email_lint.py` after a rebuild. It opens the dashboard, generates every email (350 on Oct 30, 2026) and fails if any contains internal wording. Fix the template, not the check.

## Rule for the Churn risk and AR Rundown tabs

Both tabs show only the accounts of the Client Success Manager whose dashboard is open (you by default, or the person picked in the CSM dropdown). There is no "All accounts" view in them: the Managers View is where the whole team is compared. After a rebuild, run `python3 scope_check.py`; it opens the file as four different CSMs and fails if either tab shows anyone else's account.

## Quality checks before the file goes to anyone else

1. **Dates in hand-written text.** Tasks, Gong follow-ups and notes carry dates that were true on the build day. On each rebuild, move the hand-written task due dates to the rebuild date, and write "closes 11/2" or "last updated 10/15" instead of "six days out" or "78 days ago". Dates inside sentences use the friendly form (Oct 1, 2031), not 2031-10-01.
2. **Counts in sentences.** Counts such as the number of open CTAs, Health Drops, urgent cases or accounts must come from the data (the CTAs tab and the header do), not from typed numbers. If a typed number is unavoidable, date it.
3. **Open cases and CTAs.** Re-pull the open High and Urgent cases (`CaseNumber, Id, Account.Name, Priority, Status, CreatedDate, LastModifiedDate, Owner.Name`) and rewrite the urgent-case task from them. Drop any Health Drop CTA row whose account no longer has an open Health Drop.
4. **Header and bar.** The header shows the account count and the oldest source date from the data bar. Check that it matches.
5. **Run the checks:** `python3 text_sweep.py` (looks for undefined, NaN, stray punctuation and similar in every tab as two CSMs), `python3 email_lint.py` and `python3 scope_check.py`.
6. **Read the emails.** Fill nothing in, but read a sample: they should sound like a person writing to a customer, use only the customer's own figures, what came up on calls and support, and cited industry sources, and never use internal vocabulary.

## Weekly, with no chat at all (recommended)

Claude Code can run this on a schedule in the cloud, with your Gainsight, Salesforce and Ironclad connectors, and no one in the loop. Per the Claude Code documentation (code.claude.com, "Automate work with scheduled tasks", a research preview): a scheduled task is a saved prompt plus one or more GitHub repositories plus connectors, it runs on a recurring schedule in an Anthropic-managed cloud session, and it keeps working when your laptop is closed. It is available on Pro, Max, Team and Enterprise plans and is created at claude.ai/code/routines or with `/schedule` in the CLI.

Setup, about 15 minutes:
1. Create a private GitHub repository. Put `csm_dashboard.html`, `Dashboard_Rebuild_Runbook.md` and `rebuild_helpers.py` in it.
2. At claude.ai/code/routines click **New task**. Select the repository, keep the Gainsight, HST Salesforce and Ironclad connectors, and remove the others.
3. Prompt: "Rebuild csm_dashboard.html by following Dashboard_Rebuild_Runbook.md from start to finish without asking questions. Commit the result to the main branch and put a short summary of what changed in the commit message."
4. Trigger: weekly, for example Monday at 6:07 AM (pick a few minutes past the hour so it starts on time).
5. Click **Run now** once and read the run in the History list to check it end to end before relying on the schedule.

Things to confirm first: your organisation must allow scheduled tasks and cloud sessions (an Owner controls this in Organization settings), the repository needs GitHub access, and the task runs as you, so connector access follows your own permissions. Runs count against your usage limits. Open the committed `csm_dashboard.html` from the repository to use the new copy. A scheduled task rebuilds the file; the dashboard's own Refresh data button (needs Claude) still refreshes the five live datasets between rebuilds.

## Group 1: refreshed by the Refresh data button (queries verified)

| Dataset | Source | Notes |
|---|---|---|
| Overdue CTA counts by CSM | Gainsight `call_to_action`, open and overdue, grouped by owner, type and priority, for the 12 CSMs | Risk = type Risk. Objective = all other types. High = priority High. Oldest = earliest due date. |
| Renewal opportunities | Salesforce Opportunity: type Renewal - Upsell or Renewal - Downsell, or Primary Product Interest = Renewal, with a Contract End Date in this year or next, plus open renewals with no end date (not Place Holder) | Test accounts and churn opportunities are left out. Shaped by `renBuild`. |
| CSQL by CSM | Salesforce Opportunity in campaign `701Ub00000kpsGpIAI` (Client Success - CSQL 2026) | Status: w won, l closed lost or unqualified, o open. Only the 12 CSMs, created this year. |
| Churn risk | Salesforce Opportunity: Opportunity Type = Churn, not Unqualified, open or close date today or later | Shaped by `crlBuildCh`, which reproduces the file's list exactly. |
| AR Rundown | Salesforce Opportunity: stage AR Rundown Initiated, Approved or Completed | Shaped by `crlBuildAr`, which reproduces the file's list exactly. |

## Group 2: needs a rebuild (not covered by the button)

| Dataset | Source | Status |
|---|---|---|
| Account scorecard (the CSV): ARR, current and previous health, NPS, denial rate, AR over 90 days, last bill, Clariti login, product flags, open CTAs, RCM provider | Gainsight `company`, where Client_Success_Manager__gc = 1P0159VMAQP7VT8LSY9VU5ZKP0OQMQSYGBDW and Status = 1I007RA46FD2CEFUZS4UTYXM885XIUPFTKZK, sorted by ARR, limit 200. Select: Gsid, Name, Arr, SfdcAccountId, Nps, Csat, CurrentScore and PreviousScore label and score, Trend, TotalOpenCtas, PM_Last_Bill_Date__gc, PM_Cancelled_Visits__gc, Total_AR_Over_90_Days_Old__gc, Claim_Denial_Rate__gc, Bad_Debt__gc, Clariti_Last_Login_Date__gc, the Core_* product flags, Account_Segmentation__gc, Package_End_Date__gc, Synergen_Maturity_Score__gc, RCM_Providers__gc | Column order: name, ARR, health, previous health, NPS, denial %, AR over 90 %, last bill, Clariti login, eChart, Clariti, Case Coordination, open CTAs, RCM provider, PM. Re-pulled Oct 29, 2026 (140 active accounts in Gainsight; the dashboard holds 137 and keeps its own account names). The mapping above was checked against the Oct 27 file: NPS, denial, AR, product flags and RCM matched exactly, so only real changes came through (last bill dates, ARR, previous health, open CTAs). Earlier hand corrections were typo fixes, not judgment calls. Empty health = N. A Clariti login of 1900-01-01 = blank. The date lives in `SC_ASOF` in the template. Three accounts exist in Gainsight but not in the dashboard (Orthopedic Sports Institute, Golden State Orthopedics & Spine, Bellevue Hand Surgery (Closed)); adding an account means adding it to every name-keyed dataset. |
| NPS and CSAT dates, survey detail | Gainsight and Salesforce survey records | Re-derive from the first build session; verify against the file. |
| Support cases: open cases now, cases closed in the last 90 days, and the 90 days compared with the 90 before | Salesforce Case for `Account.Client_Success_Manager__r.Name = 'Jacobson Menashe'`. Pull three row-level queries (each is stored as a file, so nothing needs retyping): cases created in the last 91 days, cases created in the 91 days before, and open cases created before that. | Re-pulled Oct 29, 2026 (`SUPPORT`, `URGENT_OPEN`, `CASES_L90`, `CASES_P90`). Definitions, checked against the Oct 27 file: `SUPPORT[name] = [open now (all open cases), closed among the cases created in the last 91 days (blank when fewer than 6), note]`. The note is "N URGENT open" or "N HIGH open" from open cases by priority, else "N urgent closed in 90 days", else the earlier hand-written note. `URGENT_OPEN` is u or h by the highest open priority. Case Subject is restricted in the connector. The support topic groups (Case Reason and Product) were not re-pulled. |
| Billing detail per account (`ACCT_BILL`) | The same Gainsight fields as the scorecard: last bill date, AR over 90 days, denial rate, keyed by Salesforce Account Id | Regenerated Oct 29, 2026 from the refreshed scorecard (AR and denial matched the old values exactly; last bill dates are newer). |
| Practice management numbers per account (`ACCT_PM`) | Gainsight `company`: SfdcAccountId, PM_Bill_Amount__gc, PM_Scheduled_Cases__gc, PM_Cancelled_Cases__gc, Days_Sales_Outstanding_DSO__gc, Arr, where CSM = you, Status active and PM_Bill_Amount__gc is not null. Shape: `[billed, scheduled cases, cancelled cases, DSO]` | Checked Oct 29, 2026: the first 50 accounts matched the file exactly (these roll up monthly). Re-pull all three pages on a rebuild. |
| eChart use per account (`ACCT_ECH`) | Gainsight `company`: SfdcAccountId, eChart_Scheduled_Cases__gc, eChart_Monthly_eChart_Visits__gc, eChart_Active_eChart_Users__gc, eChart_New_Users__gc, eChart_Tasks_Older_than_7_Days__gc, Percent_Over_10_Days_to_Complete__gc, eChart_First_Chart__gc, Arr, where Current_Active_eChart_ARR__gc > 0. Shape: `[cases, visits, users, new users, tasks over 7 days, percent over 10 days, first chart]` | Re-pulled Oct 29, 2026 (57 accounts). Only the tasks-over-7-days figure changes day to day. |
| Open opportunities per account (`ACCT_OPPS`) | Salesforce: `SELECT AccountId, COUNT(Id) n, SUM(Net_ARR__c) arr FROM Opportunity WHERE IsClosed = false AND AccountId IN (SELECT Id FROM Account WHERE Client_Success_Manager__c = '005Ub00000H3pYrIAJ') GROUP BY AccountId`. Shape: `[count, net ARR]` | Re-pulled Oct 29, 2026 (104 accounts; 3 changed). |
| Product flags per account (`ACCT_PRODS`) | Salesforce Account Current Active ARR fields, as six flags: PM, eChart, Clariti, Patient Engagement, Dashboards, Pay | Not re-pulled. The field names were not recorded, and the Gainsight Core_* product flags disagree on 14 accounts, so they are not a substitute. Find the field names from an Account describe before refreshing. |
| NPS and CSAT dates (`NPS_ROWS`) | Gainsight `company`: Nps, NpsLastUpdated, Csat, CsatLastUpdated | Checked Oct 29, 2026 with a filter on dates since Oct 27: no updates, so the data is current (`NPS_ASOF`). A filtered query like this is the cheap way to check for changes. |
| Contracts for the account list (`CONTRACTS`, `OPEN_RENEWALS`) | Salesforce Opportunity for `Account.Client_Success_Manager__r.Name = 'Jacobson Menashe'`, stage Finance Approved, Closed Won or Place Holder, with a Contract End Date | Checked Oct 29, 2026 against a fresh pull: all 13 rows still match on end date, ARR and stage. The list is curated (the larger contract ends from about Aug 2026 to Apr 2027, not the small interface and data add-ons, with a hand-written note on each), so a rebuild checks it rather than regenerating it. The renewal rows overlap with the Renewal Opportunities data. |
| Engagement timeline (last logged contact per account, `ENG`) | Gainsight `activity_timeline` grouped by company: MAX(ActivityDate) and COUNT, types Call, Meeting and Email, for the CSM's active companies, sorted by last touch ascending. Three result pages. | Re-pulled Oct 29, 2026. `ENG` keeps the accounts whose last touch is before today minus 30 days, plus accounts with none at all (`[null, 0]`), keyed by the dashboard's account name. Days since contact count from `ENG_DAY`. |
| Gainsight CTAs and success plans for my accounts | Gainsight `call_to_action` and success plans, per company | Script: `gs/build_gs_data.py`. |
| Overdue CTA lists and the largest accounts with an overdue CTA | Gainsight `call_to_action`, open and overdue, 12 CSMs | The 10 oldest per CSM and the top 30 by ARR. |
| Other CSMs' portfolios (`CSM_SUM`, `CSM_TOP`) | Gainsight `company`. Health and ARR: one grouped query (group by Client_Success_Manager__gr.Name and CurrentScore__gr.Label, COUNT and SUM(Arr), active status). Largest accounts: per CSM, limit 15, sorted by Arr descending, with Name, Arr, Nps, NpsLastUpdated, Csat, CsatLastUpdated and the health label. | Health counts, ARR and the health of the 15 largest accounts re-pulled Oct 29, 2026. Health moved a lot between Oct 28 and 29 (a scoring run: Cathy's green accounts went from 23 to 234). The NPS, detractor and CSAT counts in `CSM_SUM` were not re-pulled (10 surveys changed across 5 CSMs since Oct 28). |
| SSO status by center | Salesforce and Gainsight | Last pulled Oct 29, 2026. |
| Gong call summaries | Gong | Four accounts were read for the last 90 days. |
| Gainsight company ids for accounts outside the portfolio | Gainsight `company` by SfdcAccountId | Used for the links on the churn, AR Rundown and renewal pages. |

## On demand, not part of a rebuild

Contracts (Ironclad) load when someone clicks Load contracts on an account page, and are then shared.

## Where the earlier pull methods are

The first build (Oct 27, 2026) and the later sessions kept their queries and patch scripts in the conversation transcripts. Search them for the dataset's name before re-deriving a query.

## Support topics, contract terms and Gong (refreshed or checked Oct 29, 2026)

| Dataset | Method |
|---|---|
| Support topic chips (`AG_POOL`), shared issue groups (`ISSUE_GROUPS`), escalation types (`ESC_GROUPS`) and accounts with repeated issues (`ACCT_ISSUES`) | Two row-level Salesforce case queries, one for the last 91 days and one for the 91 before, each with `Account.Client_Success_Manager__c = '005Ub00000H3pYrIAJ'` and the fields `Id, AccountId, Account.Name, Product__c, Case_Reason__c, Escalation_Type__c, Status, Priority, Type, Origin, CreatedDate, IsClosed` (the result is stored as a file, so read it with `sf_records`). Cases and distinct accounts by (`Product__c`, `Case_Reason__c`) fill `ISSUE_GROUPS`, with the group-to-reason mapping in the script used on Oct 29 (for example clElig = Clariti / Eligibility, ccInt = Case Coordination / Integration Questions / Issues, clCon = Clariti / Contracts and Fee Schedules Adjustments). `ESC_GROUPS` uses `Escalation_Type__c` (Interops - Data Flow Internal/External Integration, Product - Bug, Techops, Interops - Monitor integration issues, Product - Latency issues, Product - Feature Limitation/Enhancement, Product - Issues due to recent Upgrade/Patch, Data Fix). `ACCT_ISSUES` lists accounts with 3 or more cases in one reason group, or 2 or more in bug, latency, internal or external integration, in the last window. Each chip's percent change is `round((last window - window before) / window before * 100)`, which reproduced the Oct 27 values exactly. The article numbers and attach counts on the chips were not re-pulled. |
| Contract terms (`ACCT_TERMS`) | Checked, not regenerated: the two aggregate queries listed in the dataset notes were run for the accounts whose won opportunities changed overnight, and the file matched them on close date, term, start and end. Run the same check for every account whose won opportunities were modified since the last build. |
| Gong summaries (`GONG`) | Checked with `ask_account` and a window starting at the last build date: no new calls or substantive emails on the four accounts, so the summaries stand. If there is new activity, re-read it and rewrite that account's entry. |
| Product flags (`ACCT_PRODS`) | Verified Oct 29 by spot check. Flags are Account `Current_Active_<product>_ARR__c > 0` in the order PM, eChart, Clariti, Patient Engagement, Dashboards, Pay. |

## Gotchas learned

- The Salesforce connector does not allow `Subject` on Case. Use status, priority, dates and account.
- Gainsight `run_query` needs the sort field in the select list.
- Gainsight accounts can be renamed and new ones appear (140 now, 137 in the dashboard). Match by the dashboard's names with `ALIAS`, and list new accounts in the summary instead of adding them: adding an account means adding it to every name-keyed dataset.
- Gainsight re-scores health in a batch, so health counts can jump overnight. That is real, not an error.
- Inside the dashboard file, `const` data arrays are read at load time, so a rebuild changes the file, not a running page. The Refresh data button saves its own copies and discards them when a newer build replaces the file.
