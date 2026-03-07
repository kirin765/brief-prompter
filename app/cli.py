from __future__ import annotations

import argparse
import asyncio
import json

from .config import get_settings
from .schemas.jobs import JobOut
from .services.pipeline import build_pipeline
from .db.session import init_db


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("brief-prompter CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    run_once = sub.add_parser("run-once", help="Run pipeline one time")
    run_once.add_argument("--dry-run", action="store_true", help="Skip external API calls")

    refresh = sub.add_parser("refresh-brief", help="Read latest brief")

    sub.add_parser("list-jobs", help="List recent jobs")

    retry = sub.add_parser("retry-job", help="Retry a failed job")
    retry.add_argument("job_id")

    sub.add_parser("dry-run", help="Run dry-run pipeline once")

    return parser


def _print_jobs(jobs):
    payload = [JobOut.model_validate(job).model_dump(mode="json") for job in jobs]
    print(json.dumps(payload, default=str, indent=2))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    settings = get_settings()
    pipeline = build_pipeline(settings)
    init_db(settings.database_url)

    async def do_run_once(dry_run: bool = False):
        job = await pipeline.run_once(dry_run=dry_run)
        print(json.dumps({"job_id": job.job_id, "status": job.status}, default=str))

    async def do_refresh_brief():
        brief = await pipeline.refresh_brief_only()
        print(brief)

    async def do_retry(job_id: str):
        job = await pipeline.retry_job(job_id)
        print(json.dumps({"job_id": job.job_id, "status": job.status}, default=str))

    async def do_list_jobs():
        _print_jobs(pipeline.list_jobs())

    if args.command == "run-once":
        asyncio.run(do_run_once(dry_run=args.dry_run))
    elif args.command == "refresh-brief":
        asyncio.run(do_refresh_brief())
    elif args.command == "list-jobs":
        asyncio.run(do_list_jobs())
    elif args.command == "retry-job":
        asyncio.run(do_retry(args.job_id))
    elif args.command == "dry-run":
        asyncio.run(do_run_once(dry_run=True))


if __name__ == "__main__":
    main()
