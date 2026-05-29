"""Daily Feed CLI — entry point."""

import argparse
import json
import sys

import httpx

from cli import api_client


def _err(msg: str):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def _output(data, fmt: str):
    """Print data as compact JSON (default) or pretty-printed JSON."""
    if fmt == "pretty":
        print(json.dumps(data, indent=2, default=str))
    else:
        print(json.dumps(data, default=str))


def main():
    parser = argparse.ArgumentParser(
        prog="daily-feed",
        description="Daily Feed CLI — query your personalized news backend",
    )
    parser.add_argument(
        "--format",
        choices=["json", "pretty"],
        default="json",
        help="Output format: json (compact) or pretty (indented, default: json)",
    )

    sub = parser.add_subparsers(dest="command")

    # briefing
    p_briefing = sub.add_parser("briefing", help="Run full pipeline digest")
    p_briefing.add_argument(
        "--time",
        choices=["morning", "evening"],
        default="morning",
        help="Briefing time of day (for display only, not used by backend)",
    )

    # articles
    p_articles = sub.add_parser("articles", help="List articles")
    p_articles.add_argument("--category", help="Filter by category")
    p_articles.add_argument("--source", help="Filter by source")
    p_articles.add_argument("--limit", type=int, default=20, help="Max results")

    # search
    p_search = sub.add_parser("search", help="Search articles")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--limit", type=int, default=10, help="Max results")

    # article (single)
    p_article = sub.add_parser("article", help="Get a single article")
    p_article.add_argument("id", type=int, help="Article ID")

    # sources
    sub.add_parser("sources", help="List sources")

    # digests
    p_digests = sub.add_parser("digests", help="List recent digests")
    p_digests.add_argument("--limit", type=int, default=10, help="Max results")

    # trends
    sub.add_parser("trends", help="Detect emerging trends")

    # stats
    sub.add_parser("stats", help="Show system stats")

    # fetch
    sub.add_parser("fetch", help="Trigger RSS fetch")

    # pipeline
    p_pipeline = sub.add_parser("pipeline", help="Run a pipeline task")
    p_pipeline.add_argument(
        "task_type",
        help="Pipeline task type (fetch, process, digest, full, trends, cluster, synthesize, memory_sync)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    fmt = args.format

    try:
        if args.command == "briefing":
            data = api_client.run_pipeline("full")
            _output(data, fmt)

        elif args.command == "articles":
            data = api_client.list_articles(
                category=args.category, source=args.source, limit=args.limit
            )
            _output(data, fmt)

        elif args.command == "search":
            data = api_client.search_articles(query=args.query, limit=args.limit)
            _output(data, fmt)

        elif args.command == "article":
            data = api_client.get_article(args.id)
            _output(data, fmt)

        elif args.command == "sources":
            data = api_client.get_sources()
            _output(data, fmt)

        elif args.command == "digests":
            data = api_client.get_digests(limit=args.limit)
            _output(data, fmt)

        elif args.command == "trends":
            data = api_client.run_pipeline("trends")
            _output(data, fmt)

        elif args.command == "stats":
            data = api_client.get_stats()
            _output(data, fmt)

        elif args.command == "fetch":
            data = api_client.trigger_fetch()
            _output(data, fmt)

        elif args.command == "pipeline":
            data = api_client.run_pipeline(args.task_type)
            _output(data, fmt)

    except httpx.ConnectError:
        _err(f"Cannot connect to Daily Feed backend at {api_client.BASE_URL}")
    except httpx.HTTPStatusError as exc:
        _err(f"HTTP {exc.response.status_code}: {exc.response.text}")
    except httpx.TimeoutException:
        _err(f"Request timed out connecting to {api_client.BASE_URL}")
    except Exception as exc:
        _err(str(exc))
