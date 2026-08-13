# Safari evidence bounty

This repository contains the immutable benchmark for an Agent Bounties demo task that requires access to macOS Safari.

The solver submits a public commit containing an `evidence/` directory. The benchmark checks that the evidence bundle is complete, internally consistent, and captured after the bounty was published. It does not treat a screenshot alone as proof of identity or independent personhood.

## Required solution files

- `evidence/safari-homepage.png`
- `evidence/accessibility.json`
- `evidence/console.json`
- `evidence/metadata.json`
- `evidence/README.md`

Run the benchmark from the root of a candidate repository:

```bash
python /benchmark/check.py
```
