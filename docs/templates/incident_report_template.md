# Incident Report: [Incident Name]

## Incident Summary

**Date:** YYYY-MM-DD
**Time:** HH:MM (Timezone)
**Duration:** X hours Y minutes
**Severity:** P0 / P1 / P2 / P3
**Status:** Resolved / Investigating / Monitoring
**Incident Commander:** [Name]

## Impact

**Systems Affected:**
- [ ] Production data pipeline
- [ ] Staging environment
- [ ] Development environment
- [ ] Data quality
- [ ] Reporting/Analytics

**Business Impact:**
- Users affected: [number/description]
- Data affected: [tables/models]
- Reports impacted: [list]
- Revenue impact: [if applicable]

**Metrics:**
- Downtime: X hours
- Data delay: X hours
- Records affected: X rows

## Timeline

| Time | Event | Action Taken |
|------|-------|--------------|
| HH:MM | Issue detected | Alert triggered |
| HH:MM | Team notified | On-call engineer paged |
| HH:MM | Investigation started | Reviewed logs |
| HH:MM | Root cause identified | Found issue in X |
| HH:MM | Fix applied | Deployed patch |
| HH:MM | Verification | Ran tests |
| HH:MM | Issue resolved | Monitoring |

## Root Cause

### What Happened
[Detailed explanation of what went wrong]

### Why It Happened
[Root cause analysis]

### Contributing Factors
- Factor 1
- Factor 2
- Factor 3

## Detection

**How was it detected?**
- [ ] Automated alert
- [ ] User report
- [ ] Monitoring dashboard
- [ ] Manual check
- [ ] Other: [specify]

**Alert/Monitoring:**
[Details about alert that fired or should have fired]

## Resolution

### Immediate Fix
[What was done to resolve the incident]

```bash
# Commands used
git revert abc123
./scripts/deploy.sh production prod
```

### Verification
[How the fix was verified]

```bash
# Verification commands
dbt test --select affected_models
python scripts/smoke_tests.py
```

## Prevention

### Short-term Actions
- [ ] Action 1 - Owner: [Name] - Due: [Date]
- [ ] Action 2 - Owner: [Name] - Due: [Date]
- [ ] Action 3 - Owner: [Name] - Due: [Date]

### Long-term Actions
- [ ] Action 1 - Owner: [Name] - Due: [Date]
- [ ] Action 2 - Owner: [Name] - Due: [Date]
- [ ] Action 3 - Owner: [Name] - Due: [Date]

## Lessons Learned

### What Went Well
- Item 1
- Item 2
- Item 3

### What Could Be Improved
- Item 1
- Item 2
- Item 3

### Action Items
1. **Monitoring:** [Improvements needed]
2. **Testing:** [Additional tests to add]
3. **Documentation:** [Updates needed]
4. **Process:** [Process improvements]
5. **Training:** [Team training needs]

## Related Issues

**Similar Past Incidents:**
- [Link to incident #1]
- [Link to incident #2]

**Related Tickets:**
- [Link to Jira/GitHub issue]

## Attachments

- [ ] Error logs
- [ ] Screenshots
- [ ] Database queries
- [ ] Monitoring graphs
- [ ] Code changes

## Sign-off

**Reviewed by:**
- [ ] Incident Commander
- [ ] Team Lead
- [ ] Engineering Manager

**Date Closed:** YYYY-MM-DD
