# weekly synthesis

## When to use

The user asks for a weekly recap, "this week in review," or a periodic summary.

## Steps

1. Call `list_articles(limit=100)` to get the week's articles. Adjust the limit based on how active the user's sources are.
2. Call `detect_trends()` to find topics that gained momentum over the week.
3. Call `cluster_articles()` on the results to group by topic.
4. Call `get_user_interests()` to contextualize the synthesis.
5. For the top 5 clusters, call `synthesize_topic(topic, article_ids)`.
6. Call `get_sources()` to see which sources were active.
7. Present the synthesis using the output format below.

## Output format

Clean summary. Topic-driven. Scannable.

### Week's top 5 stories

Pick the 5 topics with the most coverage or highest relevance to the user. For each:

- Topic header
- 2 to 3 sentence synthesis from `synthesize_topic()`
- Number of articles and sources that covered it

### Trending topics

From `detect_trends()`, list topics that grew over the week. For each:

- Topic name
- Trajectory (growing, peaked, fading)
- Whether it aligns with the user's interests

### Watch list

Recommend 2 to 3 topics the user should follow next week. Base these on:

- Trends that are still growing
- Topics that match the user's interests but had light coverage
- Stories that are likely to develop further

### Source activity

From `get_sources()`:

- Which sources published the most this week
- Any sources that went inactive
- Coverage gaps (user interests with no matching articles)

## Error handling

- If `list_articles()` returns fewer than 10 articles, tell the user there isn't enough data for a meaningful weekly synthesis. Offer a daily summary instead.
- If `detect_trends()` fails, skip the trending section and focus on the top stories and clusters.
- If `cluster_articles()` produces only one cluster, present the articles as a flat list organized by date.
