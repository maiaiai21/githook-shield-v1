# GitHook Shield

GitHook Shield stops hardcoded secrets and broken code before they reach a Git repository, then checks them again in CI. Scan results are stored in cloud-style storage, alerts go through a notification topic, and a live dashboard shows activity as it happens.

The project is a DevSecOps assignment. Everything runs locally or in GitHub Actions. It needs no AWS account, because LocalStack emulates the AWS services.

## What it does

- **Blocks secrets at commit time.** A pre-commit hook runs a custom scanner on staged changes. It catches known token formats (AWS, GitHub, Slack, Stripe, Google, private keys) and high-entropy values assigned to credential-like names such as `password` or `api_key`.
- **Blocks broken code at commit time.** Staged `.py`, `.json`, and `.sh` files must pass a syntax check.
- **Re-checks everything in CI.** GitHub Actions runs the tests, scans every tracked file with the same scanner, scans the full Git history with TruffleHog, validates Terraform, builds the Docker image, and scans it with Trivy.
- **Stores reports and sends alerts.** CI uploads scan reports to an S3 bucket and publishes failure alerts to an SNS topic. Terraform creates both.
- **Shows activity live.** A dashboard reads the scan log and updates within seconds.
- **Measures itself.** A labeled dataset compares the scanner with Gitleaks and detect-secrets.

## Architecture

```
Developer
   │ git commit
   ▼
Pre-commit hook ──► Scanner (secretscan.py) ──► scan-log.json ──► Dashboard
   │
   │ git push
   ▼
GitHub Actions
   ├── test              unit tests (scanner and app)
   ├── secret-scan       custom scanner + TruffleHog (full history)
   ├── terraform         fmt, init, validate
   ├── build-and-scan    Docker build, Trivy scan, report upload to S3
   └── alert-on-failure  SNS alert when any job fails

Terraform ──► LocalStack (S3, ECR, SNS, EC2, IAM, STS)  or real AWS
```

## Project structure

```
.github/workflows/ci.yml     CI pipeline
app/                         Flask service, Dockerfile, requirements
dashboard/                   live dashboard and its README
docker-compose.yml           LocalStack
evaluation/                  labeled dataset, evaluation script, results
hooks/pre-commit             commit-time hook
scanner/secretscan.py        custom secret scanner and syntax checks
scripts/                     install, demo, live sample, upload, and alert scripts
terraform/                   AWS resources (S3, ECR, security group, SNS)
tests/                       unit tests for the scanner and the app
```

## Quick start

You need Python 3.12 or newer and Git. Docker, Terraform 1.9.8, and the AWS CLI are only needed for the LocalStack demo.

```
pip install -r app/requirements.txt
bash scripts/install-hooks.sh
python3 -m unittest discover -s tests -v
```

The unit tests should end with `OK`. The hook is now active for this repository.

## Components

### Secret scanner (`scanner/secretscan.py`)

- **Token rules:** fixed patterns for AWS access key IDs (`AKIA`, `ASIA`), GitHub tokens (`gh[pousr]_`), Slack tokens (`xox`), Stripe live keys (`sk_live_`), Google API keys (`AIza`), and PEM private key headers.
- **Assignment rule:** flags a quoted value of 8 or more characters assigned to a credential-like name, when the value has a Shannon entropy of at least 3.0 bits per character.
- **Allowlist:** placeholders such as `changeme`, `your_api_key_here`, and `<...>`, plus the AWS documentation example keys, are ignored.
- **Syntax checks:** `.py` files must parse, `.json` files must load, and `.sh` files must pass `bash -n`.
- **Output:** findings show the file, line, and rule, with the secret masked. The exit code is 1 when anything is found.

Run it on files directly, or on staged changes:

```
python3 scanner/secretscan.py path/to/file.py
python3 scanner/secretscan.py --staged --log scan-log.json
```

### Pre-commit hook (`hooks/pre-commit`)

Runs the scanner on staged changes and appends results to `scan-log.json`. Install it once per clone with `bash scripts/install-hooks.sh`.

Bypassing the hook with `git commit --no-verify` skips it entirely. CI catches what gets through.

### CI pipeline (`.github/workflows/ci.yml`)

Runs on pushes and pull requests to `main`.

| Job | What it does |
|---|---|
| `test` | Runs the unit tests and a compile check |
| `secret-scan` | Runs the custom scanner on every tracked file and TruffleHog on the full history |
| `terraform` | Checks formatting, runs `init -backend=false`, and runs `validate` |
| `build-and-scan` | Builds the Docker image, scans it with Trivy (fails on fixable HIGH and CRITICAL findings), and uploads the report to S3 |
| `alert-on-failure` | Publishes an SNS alert when any job fails |

Steps that need AWS settings skip quietly when those settings are missing, so the pipeline still passes on a fresh fork.

### Application (`app/`)

A small Flask service with `/` and `/health` endpoints. The Dockerfile runs it as a non-root user on `python:3.12-slim`.

```
python3 app/app.py
curl http://localhost:5000/health
```

### Infrastructure (`terraform/` and `docker-compose.yml`)

Terraform creates:

- an S3 bucket for scan reports, with versioning, encryption, and public access blocked
- an ECR repository with immutable tags, scan-on-push, and a lifecycle rule that keeps the last 10 images
- a security group that allows the app port from a private network range
- an SNS topic for alerts, with an optional email subscription

LocalStack runs the same resources locally. Set `use_localstack = true` (the default) to point the provider at `http://localhost:4566`. To use real AWS, set it to `false` and configure credentials.

```
sh scripts/localstack-demo.sh
```

This starts LocalStack, applies Terraform, uploads a sample report, and publishes a sample alert. The script prints the topic and bucket names. A sample alert has no subscriber, so it doesn't show up anywhere else.

### Dashboard (`dashboard/`)

A single page that shows scan activity: a live feed, KPI tiles, a rule breakdown, and a comparison table. It refreshes every 5 seconds and falls back to sample data when there's no log.

```
python3 -m http.server 8000
```

Open `http://localhost:8000/dashboard/`. See [`dashboard/README.md`](dashboard/README.md) for details and the live demo script.

### Evaluation (`evaluation/`)

`make_dataset.py` generates 30 files with one synthetic secret each, and 30 clean files with look-alike strings. The data uses a fixed seed and is gitignored, because it contains fake secrets.

`run_eval.py` runs our scanner, Gitleaks, and detect-secrets on the dataset and writes `results.md` and `results.json`.

```
python3 evaluation/make_dataset.py
python3 evaluation/run_eval.py
```

Gitleaks needs its binary on the PATH, and detect-secrets needs `pip install detect-secrets`. Tools that aren't installed are skipped.

### Demo (`scripts/demo.sh`)

Runs in a temporary repository, so your project is untouched. It shows a clean commit accepted, a hardcoded password blocked, a syntax error blocked, and a `--no-verify` bypass that goes through.

```
sh scripts/demo.sh
```

## Results

Evaluation on the labeled dataset (30 secret files, 30 clean files):

| Tool | Precision | Recall | F1 | False positives |
|---|---|---|---|---|
| GitHook Shield (ours) | 1.00 | 0.77 | 0.87 | 0 |
| Gitleaks | 1.00 | 0.80 | 0.89 | 0 |
| detect-secrets | 0.61 | 0.93 | 0.74 | 18 |

- Our scanner misses npm, Mailgun, and Twilio formats, which we didn't implement, and short passwords that fall below the entropy threshold.
- Gitleaks misses the PEM header case that our scanner catches.
- The dataset is small. Treat these numbers as indicative, not conclusive.

Scan times on the dataset are about 0.003 seconds for our scanner, about 1.4 seconds for Gitleaks, and about 1.6 seconds for detect-secrets.

## Known limitations

- `git commit --no-verify` skips the local hook. CI is the second line of defense.
- Pattern-based detection misses secrets in formats it doesn't know, and unusual names.
- A short password below the entropy threshold passes. The demo shows this, and the threshold is deliberately unchanged to avoid more false positives.

## Repository secrets (for real AWS)

The CI steps that upload reports and publish alerts read these secrets. Without them, those steps skip:

- `REPORTS_BUCKET`
- `SNS_TOPIC_ARN`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

## Running the tests

```
python3 -m unittest discover -s tests -v
```

The scanner tests cover secret detection, false positives, syntax checks, and staged-mode behavior. The app tests cover `/` and `/health`.
