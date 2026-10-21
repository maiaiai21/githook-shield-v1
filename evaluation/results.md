# Scanner evaluation results

Dataset: 30 files with one synthetic secret each, 30 files with none.

Not run (tool not installed): Gitleaks, detect-secrets

| Tool | TP | FN | FP | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| GitHook Shield (ours) | 23 | 7 | 0 | 30 | 1.0 | 0.767 | 0.868 |

## Recall by secret category

| Category | GitHook Shield (ours) |
|---|---|
| aws-access-key-id | 2/2 |
| aws-secret-key | 2/2 |
| db-password-var | 1/2 |
| generic-api-key | 2/2 |
| generic-password | 1/2 |
| github-pat | 2/2 |
| google-api-key | 2/2 |
| hex-secret-key | 2/2 |
| jwt-token | 2/2 |
| mailgun-key | 1/2 |
| npm-token | 0/2 |
| private-key-header | 2/2 |
| slack-token | 2/2 |
| stripe-live-key | 2/2 |
| twilio-sid | 0/2 |

## Missed secrets

- **GitHook Shield (ours)**: pos_18_generic-password.env, pos_19_db-password-var.env, pos_23_npm-token.sh, pos_24_npm-token.py, pos_26_mailgun-key.env, pos_27_twilio-sid.env, pos_28_twilio-sid.yaml

## False positives

- **GitHook Shield (ours)**: none

## Scan time, seconds (positives dir / negatives dir)

- **GitHook Shield (ours)**: 0.002 / 0.002
