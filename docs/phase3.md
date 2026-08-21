# 📘 Phase 3: Automated CI/CD Regression Quality Gate

---

## 🎯 1. Overview & Objective

When modifying prompt templates, switching model versions (e.g. `gpt-4o` $\rightarrow$ `Llama-3.2-3B`), or tweaking RAG chunking parameters, software teams risk introducing **unintended quality regressions**.
- Standard software unit tests only verify syntax and HTTP codes (200 OK), remaining completely blind to semantic degradation, increased hallucination rates, or dropped context precision.
- Production AI engineering requires **Automated CI/CD Quality Gating** that runs golden evaluation datasets on every pull request and blocks deployment if quality thresholds regress.

**Phase 3 Goal:** Implement an automated **CI/CD Regression Quality Gate Engine** that:
1. Executes a curated golden dataset of domain test cases during pre-merge testing.
2. Compares evaluation triad metrics against pre-established baseline thresholds.
3. Computes regression deltas ($\Delta \text{Faithfulness}, \Delta \text{Relevance}$) and enforces strict release gating (Exit Code `0` = PASS, Exit Code `1` = BLOCK).

---

## 📐 2. Continuous Quality Gating Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CI/CD AUTOMATED REGRESSION GATE FLOW                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Pull Request Trigger ──► [ Golden Test Dataset Runner ]                    │
│                                    │                                        │
│                                    ▼                                        │
│                        [ Triad Metric Evaluator ]                           │
│                                    │                                        │
│                                    ▼                                        │
│                    [ Baseline Delta Comparator ]                            │
│                                    │                                        │
│                    ┌───────────────┴───────────────┐                        │
│                    ▼                               ▼                        │
│        ✓ PASS: Scores >= Threshold     ❌ FAIL: Quality Regression Detected │
│          (Exit Code: 0 -> Merge PR)      (Exit Code: 1 -> Block PR Release) │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 3. Step-by-Step Code Walkthrough

### Step 1: CI/CD Data Models (`src/ci_cd/models.py`)
- `GoldenTestCase`: Test item with `case_id`, `query`, `context`, `expected_ground_truth`, and minimum score thresholds.
- `GateStatus`: Status enum (`PASSED`, `REGRESSED`, `FAILED`).
- `RegressionGateReport`: Comprehensive summary containing total test count, pass rate, average scores, and flagged regressions.

### Step 2: Quality Gate Engine (`src/ci_cd/regression_gate.py`)
- **`run_golden_suite(candidate_generator)`:** Executes test suite asynchronously.
- **`evaluate_release_candidate(test_results)`:** Determines whether the release candidate meets enterprise production standards.

---

## 🧪 4. How to Run & Verify Phase 3

### Command:
```bash
./.venv/bin/pytest tests/test_ci_cd_gate.py
```

### Expected Output:
```text
============================== 3 passed in 0.05s ==============================
```

### What the Tests Verify:
1. `test_passing_release_candidate`: Asserts high-quality models pass all golden test cases.
2. `test_regressed_candidate_rejection`: Proves hallucinating prompt updates fail the CI gate with status `REGRESSED`.
3. `test_gate_report_generation`: Validates full markdown summary reporting.

---

## 💡 5. Technical Questions & Architectural Explanations

### Q: How do you select test cases for an enterprise golden evaluation dataset?
> **Answer:** Golden datasets are constructed by combining three sources:
> 1. **High-Frequency Production Queries:** Top 20% of representative user traffic.
> 2. **Known Historical Edge Cases & Failures:** Previous hallucinations or bug reports converted into regression tests.
> 3. **Adversarial & Multi-Hop Prompts:** Synthetically generated test cases designed to test retrieval boundary conditions and safety filters.
