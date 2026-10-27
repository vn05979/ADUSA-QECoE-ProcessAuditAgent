# Process Audit Agent

Authoring assets for the ADUSA QE Process Audit Agent, intended for Microsoft
Copilot Studio. The agent audits Waterfall and Audit (Agile) projects against
the supplied `QxYYYY DomainName QA CoE Audit Checklist.xlsx` workbook.

## Copilot Studio assets

- [`copilot-studio/agent-instructions.md`](./copilot-studio/agent-instructions.md) — agent role, input validation, audit procedure, evidence rules, and scoring.
- [`copilot-studio/agent-profile.json`](./copilot-studio/agent-profile.json) — agent name, description, conversation starters, and asset references.
- [`copilot-studio/checklists.json`](./copilot-studio/checklists.json) — checklist criteria transcribed from both workbook tabs.
- [`copilot-studio/report-schema.json`](./copilot-studio/report-schema.json) — structured audit report shape.
- [`copilot-studio/sharepoint-action-contract.json`](./copilot-studio/sharepoint-action-contract.json) — input/output contract and constraints for the SharePoint collection action.

## Set up in Copilot Studio

1. Create an agent named **Process Audit Agent**.
2. Add the contents of `copilot-studio/agent-instructions.md` as the agent instructions.
3. Add `copilot-studio/checklists.json` as a knowledge source, or make its criteria available to the agent through an equivalent governed source.
4. Create a Power Automate action named `CollectSharePointArtifacts` that implements `copilot-studio/sharepoint-action-contract.json`. Configure the SharePoint connection with organizational authentication and read-only permissions. The action must return evidence content and source links, paginate through up to 5,000 artifacts, and explicitly report access or extraction failures.
5. Connect the action to the agent and test both project types, an inaccessible URL, incomplete evidence, and a repository with pagination.
6. Configure the agent to return a report matching `copilot-studio/report-schema.json`. Validate that every finding has a source reference and that counts and compliance percentage agree.

## Compliance percentage

The report uses `Pass / (Pass + Fail) × 100`. Partial Compliance and Not
Applicable checks are excluded; all four status counts remain visible.
If there are no Pass or Fail checks, the percentage is null.

## Deployment note

These files are the agent authoring and integration specification; they do not
create or publish an agent in an organization's Copilot Studio environment.
Publishing requires an authorized tenant, configured SharePoint connection,
and the Power Automate action described above. The agent must not be treated
as operational until that connection and action have been configured and
tested.
