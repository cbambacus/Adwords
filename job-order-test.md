# Sample Job Order - Test Case

This sample job order represents data from Cloudwall for testing the AI recruitment advertising system.

## Job Order Data

```json
{
  "job_id": "CW-2024-78432",
  "job_title": "Senior UX Designer",
  "job_description": "We're seeking a Senior UX Designer to lead the redesign of our flagship mobile banking application. You'll conduct user research, create wireframes and prototypes, and collaborate closely with product managers and engineers. The ideal candidate has 5+ years of experience in UX design, proficiency in Figma, and a portfolio demonstrating complex B2C application work. Experience with accessibility standards (WCAG 2.1) and design systems is highly valued.",
  "salary": {
    "min": 130000,
    "max": 155000,
    "currency": "USD",
    "type": "annual"
  },
  "location": {
    "city": "San Francisco",
    "state": "CA",
    "country": "USA"
  },
  "work_arrangement": "hybrid",
  "client": "FinTech Innovations Inc.",
  "employment_type": "contract-to-hire",
  "duration_months": 6,
  "start_date": "2024-03-15",
  "additional_notes": "Client prefers candidates with fintech or banking experience. Team is 3 days in-office (Tue-Thu). Budget has some flexibility for exceptional candidates. Urgent fill - client interviewing immediately."
}
```

## Test Case Coverage

| Aspect | Value | Tests |
|--------|-------|-------|
| Targeting complexity | Specific skills, industry, seniority | Keyword generation, audience targeting |
| Location | Hybrid in San Francisco | Geo-targeting + remote keyword handling |
| Budget signals | Salary range + flexibility note | Bid strategy decisions |
| Urgency | "Urgent fill" | Campaign prioritization |
| Platform fit | Professional role, high salary | Multi-platform distribution logic |
