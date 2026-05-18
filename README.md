# ARI'Lab — Advanced Review Intelligence Lab

A code review training simulator built in pure Python. Each session presents buggy or poorly written Python snippets across five categories. You write a review comment, ARI'Lab scores it against accepted keywords, shows you what a senior developer would have written, and explains why the code is problematic.

## The five categories

| Category | What it tests |
|---|---|
| Logic Bug | Off-by-one errors, wrong initialisations, incorrect operators |
| Security | SQL injection, hardcoded credentials, path traversal, missing validation |
| Performance | N+1 queries, O(n²) loops, string concatenation in loops |
| Code Smell | Magic numbers, poor naming, functions doing too much |
| Exception Handling | Bare excepts, swallowed errors, missing finally, unguarded dict access |

## Scoring

Each challenge has a set of required concepts. Your answer is checked for keyword matches

| Grade | Criteria | Points |
|---|---|---|
| FULL | Hit at least one keyword from every required concept | Full points |
| PARTIAL | Hit some but not all required concepts | Half points |
| WRONG | No concept keywords matched | Zero points |

## Difficulty levels

- JUNIOR — 10 points — common mistakes every developer should catch
- MID — 20 points — subtler issues requiring design awareness
- SENIOR — 30 points — multi-layered problems requiring system thinking

## Run it

```bash
python arilab.py
```

## File structure

```
arilab/
├── arilab.py        # Main application and GUI
├── challenges.py    # Full challenge bank
├── scorer.py        # Keyword-based scoring engine
├── database.py      # SQLite result persistence
├── requirements.txt
└── README.md
```
