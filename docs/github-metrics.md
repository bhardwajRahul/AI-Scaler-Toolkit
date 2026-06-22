# GitHub Metrics Backup

This repository includes a scheduled GitHub Actions workflow at `.github/workflows/metrics-backup.yml` that archives GitHub repository metrics into `data/metrics/`.

## What It Tracks

- Repository page views (`traffic/views`)
- Unique visitors (`traffic/views[].uniques`)
- Repository clone counts (`traffic/clones`)
- Unique cloners (`traffic/clones[].uniques`)
- GitHub Release asset download counts (`releases[].assets[].download_count`)

The Traffic API only exposes a rolling 14-day window, so the workflow stores a daily snapshot to preserve long-term history.

## Schedule

The workflow runs once per day by default:

```yaml
on:
  schedule:
    - cron: '0 0 * * *'
```

You can also trigger it manually from the GitHub Actions UI with `workflow_dispatch`.

## Required Secret

Create a repository secret named `GH_METRICS_TOKEN`.

Recommended token options:

- Classic PAT:
  - Public repository: `public_repo`
  - Private repository: `repo`
- Fine-grained PAT:
  - Repository access: target repository only
  - `Contents`: Read and write
  - `Administration`: Read-only

The workflow uses this token for both API reads and committing the archived metrics back into the repository.

## Output Files

After each run, the workflow updates these files:

- `data/metrics/snapshots/YYYY-MM-DD.json`: full daily snapshot
- `data/metrics/latest/metrics-summary.json`: latest combined JSON payload
- `data/metrics/latest/traffic.json`: latest traffic-only JSON payload
- `data/metrics/latest/releases.json`: latest releases-only JSON payload
- `data/metrics/latest/traffic-daily.csv`: latest traffic CSV export
- `data/metrics/latest/release-assets.csv`: latest release download CSV export

## JSON Shape

The daily snapshot has this high-level structure:

```json
{
  "generated_at": "2026-06-22T00:00:00.000Z",
  "repository": "owner/repo",
  "traffic": {
    "views": {
      "count": 0,
      "uniques": 0,
      "views": []
    },
    "clones": {
      "count": 0,
      "uniques": 0,
      "clones": []
    }
  },
  "releases": {
    "release_count": 0,
    "asset_count": 0,
    "total_asset_downloads": 0,
    "items": []
  }
}
```

## First Run Checklist

1. Add the `GH_METRICS_TOKEN` repository secret.
2. Push the workflow file to the default branch.
3. Open Actions and run `Archive GitHub Metrics` manually once.
4. Confirm new files appear under `data/metrics/`.
5. Review the commit created by `github-actions[bot]`.

## Notes

- If the repository has no GitHub Releases yet, the workflow still writes a release snapshot with zero assets.
- If no metrics changed since the previous run, the workflow skips the commit.
- If you do not want metrics commits on the default branch, change the workflow to commit to a dedicated branch such as `traffic`.