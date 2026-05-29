# morning briefing

## When to use

The user asks for a morning briefing, daily summary, or "what's new today."

## Steps

1. Call `get_stats()` to check system health and confirm the backend is running.
2. Call `trigger_fetch()` to pull fresh articles from all sources.
3. Call `get_briefing(time="morning")` to generate the personalized digest.
4. Call `get_user_interests()` to get the user's learned preferences.
5. Call `detect_trends()` to surface emerging topics from the latest articles.
6. Present the briefing using the output format below.

## Output format

Structure the briefing as follows. Keep it scannable. No walls of text.

### Top stories

Pick 3 to 5 articles with the highest relevance to the user's interests. For each:

- Headline
- One sentence on what happened
- One sentence on why it matters to the user specifically

### Trending topics

List 2 to 3 emerging trends from `detect_trends()`. For each:

- Topic name
- Brief description of the trend
- Number of articles covering it

### Interest matches

Group articles by the user's learned interests. For each interest:

- Interest name
- Number of new articles
- One standout article with a brief note on why

### Stats

End with a short line: how many new articles were fetched, how many sources were updated, and the time of the last fetch.

## Error handling

- If `get_stats()` returns an error or the backend is unreachable, tell the user the system is down. Do not continue.
- If `trigger_fetch()` returns zero new articles, say "nothing new since last check" and stop.
- If `get_briefing()` fails, fall back to `list_articles(limit=10)` and build the briefing manually from the results.
