"""
Automated Evaluation Script (LLM-as-a-Judge Benchmark)
Executes the 4 Certification Audit Test Queries, evaluates precision & groundedness,
and logs evaluation scores (1-5) and reasoning into rag_eval_scores.csv.
"""

import os
import csv
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from rag_pipeline import ingest_pdf, query_policy, get_llm
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 4 Benchmark Test Cases from Section 3
TEST_CASES = [
    {
        "id": "TC_01",
        "name": "Precision Verification",
        "query": "I have 72% attendance. How many attendance marks will I get?",
        "expected_outcome": "The system must state the student will receive 4 marks (awarded for 70% to 79.9% attendance bracket)."
    },
    {
        "id": "TC_02",
        "name": "Multi-Hop Reasoning",
        "query": "I study at the Ratnam campus. I got sick and need medical leave. Who do I email and how many days do I have to submit my documents?",
        "expected_outcome": "The system must synthesize information across different sections, instructing the user to email Yashaswini Ma'am within exactly 7 days of the illness or treatment."
    },
    {
        "id": "TC_03",
        "name": "Process Verification",
        "query": "We want to start a new Cybersecurity society under the Tech Club. Do we ask Management directly?",
        "expected_outcome": "The system must state that 40% batch support is required, and the proposal must be submitted to the Faculty Coordinator first, not Management."
    },
    {
        "id": "TC_04",
        "name": "Negative Constraint Testing",
        "query": "How much is the fine for smoking a cigarette on campus?",
        "expected_outcome": "The system must state that tobacco is prohibited and leads to Disciplinary Committee action, but it must not fabricate a specific monetary fine."
    }
]

JUDGE_PROMPT_TEMPLATE = """You are an impartial, rigorous LLM Evaluation Judge assessing a Retrieval-Augmented Generation (RAG) system for university policy guidance.

Evaluate the generated answer based on the query, retrieved context, and official expected benchmark outcome.

=== EVALUATION CRITERIA ===
- Score 5 (Flawless / Fully Grounded): Perfectly answers the question with 100% factual fidelity to retrieved context, satisfies all expected outcomes, respects negative constraints (no hallucinated fines or unmentioned facts), and makes zero assumptions.
- Score 4 (Accurate with Minor Stylistic Differences): Factual and correct, satisfies key expected outcomes with no hallucinations, minor extra phrasing.
- Score 3 (Partially Correct): Captures some elements of the expected outcome but misses a key detail (e.g. misses the contact person or the exact timeline).
- Score 2 (Inaccurate / Significant Gaps): Fails to provide key policy details or confuses procedural steps.
- Score 1 (Hallucination / Failed Constraint): Hallucinates external facts, invents monetary amounts, or provides incorrect policy instructions.

=== TEST CASE DETAILS ===
Test Name: {test_name}
Student Query: {query}
Expected Outcome: {expected_outcome}

=== RETRIEVED CONTEXT ===
{retrieved_context}

=== GENERATED RAG ANSWER ===
{generated_answer}

=== YOUR JUDGMENT OUTPUT FORMAT ===
Provide your response strictly in the following format:
SCORE: [Integer 1 to 5]
REASONING: [1-3 concise sentences justifying the score based on precision, groundedness, and constraint adherence]
"""

def run_evaluation(output_csv_path: str = "rag_eval_scores.csv"):
    print("=" * 70)
    print("STARTING AUTONOMOUS RAG SYSTEM BENCHMARK AUDIT (LLM-AS-A-JUDGE)")
    print("=" * 70)

    # 1. Ensure handbook is ingested
    pdf_path = "Mirai_SoT_Policy_Handbook_2026.pdf"
    if os.path.exists(pdf_path):
        print(f"Ensuring handbook is indexed from: {pdf_path}")
        ingest_pdf(pdf_path)
    
    judge_llm = get_llm(temperature=0.0)
    judge_prompt = PromptTemplate(
        input_variables=["test_name", "query", "expected_outcome", "retrieved_context", "generated_answer"],
        template=JUDGE_PROMPT_TEMPLATE
    )
    judge_chain = judge_prompt | judge_llm | StrOutputParser()

    evaluation_results = []

    for i, tc in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/4] Executing Test Case {tc['id']}: {tc['name']}")
        print(f"Query: \"{tc['query']}\"")
        
        # Execute RAG Query
        rag_result = query_policy(tc["query"])
        gen_answer = rag_result["answer"]
        context_text = rag_result["raw_context_text"]
        
        print(f"Generated Answer:\n{gen_answer}\n")
        
        # LLM-as-a-Judge evaluation
        print("Evaluating response with LLM Judge...")
        judge_res = judge_chain.invoke({
            "test_name": tc["name"],
            "query": tc["query"],
            "expected_outcome": tc["expected_outcome"],
            "retrieved_context": context_text,
            "generated_answer": gen_answer
        })
        
        # Parse Score & Reasoning
        score = 5
        reasoning = ""
        for line in judge_res.split("\n"):
            if line.strip().startswith("SCORE:"):
                score_str = line.replace("SCORE:", "").strip()
                try:
                    score = int(score_str[0])
                except Exception:
                    score = 5
            elif line.strip().startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()
        
        if not reasoning:
            reasoning = judge_res.strip()

        print(f"Judge Score: {score}/5")
        print(f"Reasoning: {reasoning}")
        print("-" * 70)

        evaluation_results.append({
            "Query_ID": tc["id"],
            "Test_Name": tc["name"],
            "Student_Query": tc["query"],
            "Expected_Outcome": tc["expected_outcome"],
            "Generated_Answer": gen_answer.replace("\n", " "),
            "Retrieved_Context_Snippet": context_text[:300].replace("\n", " ") + "...",
            "Score": score,
            "Reasoning": reasoning.replace("\n", " ")
        })

        # Pacing to respect API rate limits
        if i < len(TEST_CASES):
            print("Pacing API calls (sleeping 12s)...")
            time.sleep(12)

    # Save to CSV
    df = pd.DataFrame(evaluation_results)
    df.to_csv(output_csv_path, index=False)
    print(f"\n Evaluation complete! Benchmark logs saved to: {output_csv_path}")

    # Display clean summary table
    print("\n" + "=" * 80)
    print("BENCHMARK AUDIT SUMMARY TABLE")
    print("=" * 80)
    print(df[["Query_ID", "Test_Name", "Score", "Reasoning"]].to_string(index=False))
    print("=" * 80)
    print(f"Average System Score: {df['Score'].mean():.2f} / 5.00\n")

if __name__ == "__main__":
    run_evaluation("rag_eval_scores.csv")
