# FinSight AI — Manual evaluation

Date: 2026-10-01
Model: qwen3:1.7b
Report: EFERT Annual Report 2025
Scope: Consolidated main statements
Search keywords: finance cost

## Results

1. Finance cost, 2025:
   Correct amount: PKR 6,170,739 thousand.
   Initial answer omitted its page citation.

2. Finance cost versus finance cost paid, 2025:
   Correctly distinguished the two measures.
   Initial comparison omitted units.

3. Comparison after prompt update:
   Finance cost: PKR 6,170,739 thousand [PDF page 161].
   Finance cost paid: PKR 6,371,947 thousand [PDF page 162].
   Passed amount, unit, and citation checks.

4. Closing share price on December 31, 2025:
   Answer: "Not available in the provided extracts."
   Passed missing-information check.

## Limitations

These are manually reviewed examples, not an overall accuracy score.
Earlier examples have not all been rerun under the updated prompt.
PDF extraction can mix columns and omit statement headings.

## Structured-extract integration check — 2026-10-01

- Consolidated statement halves are retrieved separately.
- Finance cost and finance cost paid were correctly distinguished.
- Both 2025 amounts included currency, scale, and correct PDF citations.
- Answer passed the current citation and amount-format checks.
- Whether automatic correction was used was not recorded.
- This is one successful example, not an overall accuracy score.
