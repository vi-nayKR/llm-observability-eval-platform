# Phase 2: Automated LLM Evaluation Triad Engine (Ragas / DeepEval Standard)

---

## 1. Overview & Objective

Deploying LLM applications to production without quantitative evaluation creates severe risks of **silent hallucinations, low retrieval precision, and off-topic responses**.
- Traditional machine learning metrics (BLEU, ROUGE) fail for Generative AI because they rely on exact n-gram overlap rather than semantic truthfulness.
- Modern GenAI architectures evaluate models using the **Ragas Evaluation Triad** and **LLM-as-a-Judge** methodology to assign continuous scores ($0.0 - 1.0$) across key dimensions.

**Phase 2 Goal:** Implement an automated **LLM Evaluation Triad Engine** that computes:
1. **Faithfulness (Hallucination Metric):** Verifies all claims made in the generated answer are strictly supported by the retrieved context.
2. **Answer Relevance:** Evaluates whether the generated response directly answers the user's prompt without extraneous fluff.
3. **Context Precision:** Measures whether the highest-ranked retrieved document chunks contained the relevant ground-truth information.
4. **Toxicity & Safety Guard:** Assesses potential toxic, biased, or adversarial outputs.

---

## 2. Mathematical Modeling of the Evaluation Triad

```

 RAGAS EVALUATION TRIAD PIPELINE 

 User Query [ Context Precision ] Retrieved Contexts 
 
 
 [ Generated Answer ] [ Faithfulness (Grounding) ] 
 
 
 [ Answer Relevance ] (Score >= 0.85? APPROVED / REGRESSION FLAG) 

```

### A. Faithfulness Score Formula
Extracts atomic claims $C = \{c_1, c_2, \dots, c_N\}$ from the answer:
$$\text{Faithfulness} = \frac{\sum_{i=1}^{N} \mathbb{I}(c_i \text{ is supported by Context})}{N}$$

### B. Answer Relevance Formula
Calculates cosine similarity between user prompt embedding $\vec{e}_{\text{query}}$ and the generated answer's central semantic vector $\vec{e}_{\text{answer}}$:
$$\text{Answer Relevance} = \max\left(0, \frac{\vec{e}_{\text{query}} \cdot \vec{e}_{\text{answer}}}{\|\vec{e}_{\text{query}}\| \|\vec{e}_{\text{answer}}\|}\right)$$

---

## 3. Step-by-Step Code Walkthrough

### Step 1: Evaluation Data Models (`src/evals/models.py`)
- `EvaluationMetricType`: Enum (`FAITHFULNESS`, `ANSWER_RELEVANCE`, `CONTEXT_PRECISION`, `TOXICITY`).
- `MetricScore`: Score value ($0.0 - 1.0$), threshold pass/fail boolean, and reasoning explanation.
- `EvaluationResult`: Aggregated assessment with overall quality score and passing status.

### Step 2: Evaluation Engine (`src/evals/evaluator.py`)
- **`evaluate_faithfulness(query, context, answer)`:** Breaks answer into verifiable statements and cross-verifies against source context.
- **`evaluate_answer_relevance(query, answer)`:** Computes semantic relevance and intent overlap.
- **`evaluate_context_precision(query, context, ground_truth)`:** Measures context signal-to-noise ratio.
- **`evaluate_triad(...)`:** Executes all metrics concurrently and returns a composite quality scorecard.

---

## 4. How to Run & Verify Phase 2

### Command:
```bash
./.venv/bin/pytest tests/test_evals.py
```

### Expected Output:
```text
============================== 4 passed in 0.05s ==============================
```

### What the Tests Verify:
1. `test_faithful_answer_evaluation`: Confirms grounded answers score $\ge 0.90$ faithfulness.
2. `test_hallucination_penalty`: Validates that fabricated claims drop the faithfulness score below $0.40$.
3. `test_answer_relevance`: Confirms on-topic responses score high relevance while off-topic queries fail.
4. `test_composite_triad_evaluation`: Tests full end-to-end evaluation scorecard generation.

---

## 5. Technical Questions & Architectural Explanations

### Q: Why is Faithfulness decoupled from Answer Relevance in RAG evaluation?
> **Answer:** An answer can be 100% faithful to retrieved context while completely failing to answer the user's prompt (e.g. summarizing unrelated retrieved text). Conversely, an answer can perfectly answer the question using pretrained parametric knowledge while hallucinating details unsupported by enterprise documents. Decoupling the metrics allows pinpointing whether retrieval or generation is the root cause of failure.
