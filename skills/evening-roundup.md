# evening roundup

## When to use

The user asks for an evening summary, end-of-day digest, or "what happened today."

## Steps

1. Call `list_articles(limit=50)` to get today's articles. Use a lower limit if the user wants a quick summary.
2. Call `detect_trends()` to find emerging topics from the day's coverage.
3. Call `cluster_articles()` on the returned article IDs to group them by topic.
4. Identify the top 2 to 3 clusters by article count.
5. For each top cluster, call `synthesize_topic(topic, article_ids)` to merge coverage across sources.
6. Call `get_user_interests()` to contextualize the roundup.
7. Present the roundup using the output format below.

## Output format

Conversational but structured. Use topic headers. Keep each section brief.

### Day's top stories by topic

For each of the top 2 to 3 clusters:

- Topic header
- Synthesis from `synthesize_topic()` (3 to 5 sentences max)
- Key sources that covered it

### Emerging trends

List trends from `detect_trends()` that are new today. For each:

- Trend name
- One sentence on what's driving it
- Whether the user's interests align with it

### Worth reading tomorrow

Pick 2 to 3 articles from today that the user hasn't seen yet and that match their interests. For each:

- Headline
- Why it's worth their time

### Source activity

Brief note on which sources published the most today and any sources that went quiet.

## Error handling

- If `list_articles()` returns nothing, say "no articles found for today."
- If `cluster_articles()` fails, present the articles as a flat list grouped loosely by keyword.
- If `synthesize_topic()` fails for a cluster, present the individual article summaries from `summarize_article()` instead.
