# reference_meeting_notes.md
Document type: MEETING_TRANSCRIPT
Status: transcript
Origin: joint
Meeting: CPQ Sprint Planning and Risk Review
Date: June 11, 2026
Attendees: Dana Lee (Northstar VP Sales Operations), Miguel Arroyo (Northstar CFO), Erin Wallace (Northstar Salesforce Admin), Priya Shah (Auctor Engagement Manager), Leo Martin (Auctor CPQ Architect), Sophie Chen (Auctor Project Manager)

## Transcript Notes

Priya opened the meeting by confirming that the project remains focused on the Salesforce CPQ Release 1 scope defined in the signed SOW. The team reviewed the official August 1, 2026 go-live date and agreed that the date is still achievable if product and pricing decisions are finalized by the end of the week. Sophie noted that the July 13 through July 24 UAT window is tight and depends on Northstar protecting tester availability.

Leo summarized configuration progress. Product catalog import mapping is complete for the first data file, but approximately 90 SKUs still need corrected product family values from Northstar. Bundle configuration is in progress for the top 25 bundles, and Northstar is expected to provide the remaining bundle rules by June 17. Discount approval thresholds were confirmed in principle, but Finance still needs to provide the final margin exception table.

Dana asked whether the quote PDF could include a short distributor-facing note when a quote contains discontinued parts. Leo responded that this can be handled within the quote template if Northstar provides approved wording by June 18. Priya stated that this appears to fit within the existing quote template deliverable as long as it does not require a second template or custom component.

Miguel then raised a tentative idea about NetSuite. He said that Finance would eventually like approved quote information to flow directly into NetSuite so the billing team does not need to re-key quote totals and product lines. Leo explained that any Salesforce-to-NetSuite billing sync would involve integration design, credentials, field mapping, error handling, and testing outside the current CPQ-only release. Priya stated that NetSuite billing integration is explicitly out of scope in the signed SOW and would require a change order or Phase 2 project. Dana asked whether Auctor could at least estimate it. Priya agreed to evaluate at a high level if Northstar sends a written request, but emphasized that estimation does not make it approved scope.

The team discussed schedule risk. Sophie said that adding NetSuite billing sync before go-live would likely jeopardize the August 1 launch because UAT is designed around CPQ quote creation, pricing, approvals, and PDF generation only. Miguel acknowledged the risk and said Finance does not want to delay the core CPQ launch.

Erin noted that Northstar IT has not provisioned any NetSuite sandbox credentials for Auctor because the current project does not require NetSuite access. Priya confirmed that this is consistent with the signed SOW assumptions.

Decisions recorded:

1. August 1, 2026 remains the official production go-live date.
2. UAT will remain focused on Salesforce CPQ Release 1 capabilities.
3. Northstar will provide corrected product family values by June 13, remaining bundle rules by June 17, and final margin exception table by June 19.
4. Auctor may provide a rough estimate for NetSuite billing sync if Northstar submits a written request, but NetSuite billing sync is not approved scope and will not be added to Release 1 without signed change control.
5. Distributor-facing discontinued-part wording may be added to the single approved quote template if Northstar provides final wording by June 18.

Open risks:

- Product data corrections may delay bundle and rule testing.
- Margin exception table delay may affect approval workflow completion.
- UAT participation may be constrained by regional sales travel.
- Any attempt to add integration scope before go-live would create timeline and quality risk.
