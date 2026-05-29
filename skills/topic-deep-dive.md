# topic deep dive

## When to use

The user asks to "dig into X", "tell me more about Y", or "what's happening with Z."

## Steps

1. Call `search_articles(query=topic, limit=20)` to find relevant articles.
2. Call `cluster_articles()` on the results to identify sub-topics.
3. For each relevant article, call `summarize_article(article_id, style="concise")`.
4. Call `synthesize_topic(topic, article_ids)` to merge coverage across sources.
5. Call `explain_relevance(article_id)` for the top 3 articles to connect them to the user's interests.
6. Call `get_user_interests()` for context.
7. Present the analysis using the output format below.

## Output format

Structured analysis. Clear sections. Factual tone.

### Overview

2 to 3 sentences on what the topic is and why it's in the news.

### Key developments

Group articles by sub-topic (from clustering). For each sub-topic:

- Sub-topic header
- Brief summary of the development
- Which articles cover it (source names)

### Source coverage

From `synthesize_topic()`:

- Points of agreement across sources
- Points of disagreement or unique angles
- Which sources provided the deepest coverage

### Why it matters

From `explain_relevance()`:

- Direct relevance to the user's interests
- Broader implications
- What to watch for next

### Related topics

Suggest 2 to 3 related topics the user might want to explore. Base these on sub-topics that appeared in the clustering.

## Error handling

- If `search_articles()` returns nothing, say "no articles found for this topic" and suggest alternative search terms.
- If there are fewer than 3 articles, skip clustering and present them directly with individual summaries.
- If `synthesize_topic()` fails, present the individual summaries side by side instead.
