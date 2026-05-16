# Web Search Prompt

Search the web for public smishing data sources, prioritizing labeled datasets first.

Use queries from `SEARCH_QUERIES.md`. Start with dataset queries, then platform-specific queries, then secondary public warning pages.

For each useful result, capture:

- source name
- source URL
- source type
- whether SMS text is available
- whether labels are available
- likely language
- file format
- license or usage notes
- whether the source appears public and safe
- why it should be approved, rejected, or reviewed

Do not scrape aggressively. Do not bypass restrictions. Do not collect private personal data.

