# Scanner evaluation results

Dataset: 30 files with one synthetic secret each, 30 files with none.

| Tool | TP | FN | FP | TN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| GitHook Shield (ours) | 23 | 7 | 0 | 30 | 1.0 | 0.767 | 0.868 |
| Gitleaks | 24 | 6 | 2 | 28 | 0.923 | 0.8 | 0.857 |
| detect-secrets | 28 | 2 | 18 | 12 | 0.609 | 0.933 | 0.737 |

## Recall by secret category

| Category | GitHook Shield (ours) | Gitleaks | detect-secrets |
|---|---|---|---|
| aws-access-key-id | 2/2 | 2/2 | 2/2 |
| aws-secret-key | 2/2 | 2/2 | 2/2 |
| db-password-var | 1/2 | 1/2 | 2/2 |
| generic-api-key | 2/2 | 2/2 | 2/2 |
| generic-password | 1/2 | 1/2 | 2/2 |
| github-pat | 2/2 | 2/2 | 2/2 |
| google-api-key | 2/2 | 2/2 | 2/2 |
| hex-secret-key | 2/2 | 2/2 | 2/2 |
| jwt-token | 2/2 | 2/2 | 0/2 |
| mailgun-key | 1/2 | 2/2 | 2/2 |
| npm-token | 0/2 | 2/2 | 2/2 |
| private-key-header | 2/2 | 0/2 | 2/2 |
| slack-token | 2/2 | 2/2 | 2/2 |
| stripe-live-key | 2/2 | 2/2 | 2/2 |
| twilio-sid | 0/2 | 0/2 | 2/2 |

## Missed secrets

- **GitHook Shield (ours)**: pos_18_generic-password.env, pos_19_db-password-var.env, pos_23_npm-token.sh, pos_24_npm-token.py, pos_26_mailgun-key.env, pos_27_twilio-sid.env, pos_28_twilio-sid.yaml
- **Gitleaks**: pos_18_generic-password.env, pos_19_db-password-var.env, pos_27_twilio-sid.env, pos_28_twilio-sid.yaml, pos_29_private-key-header.yaml, pos_30_private-key-header.sh
- **detect-secrets**: pos_15_jwt-token.sh, pos_16_jwt-token.py

## False positives

- **GitHook Shield (ours)**: none
- **Gitleaks**: neg_07.sh, neg_19.sh
- **detect-secrets**: neg_01.env, neg_02.yaml, neg_04.py, neg_06.yaml, neg_07.sh, neg_08.py, neg_11.sh, neg_13.env, neg_14.yaml, neg_16.py, neg_18.yaml, neg_19.sh, neg_20.py, neg_23.sh, neg_25.env, neg_26.yaml, neg_28.py, neg_30.yaml

## Scan time, seconds (positives dir / negatives dir)

- **GitHook Shield (ours)**: 0.002 / 0.002
- **Gitleaks**: 0.477 / 0.047
- **detect-secrets**: 2.719 / 0.592
