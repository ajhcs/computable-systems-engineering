# Focused context and repair probe

Run `python3 scripts/measure_context.py`. The script duplicates the synthetic valid fixture into a two-scenario model, removes S1's `gap` producer, then compares full-model and S1-focused candidate-plus-diagnostic payloads for the **same S1 repair**. It restores that producer and reruns both reviews. The focused view retains every global declaration, requirement, and trace; verification itself still reads the complete model.

On Linux, 2026-09-29, the `regex-wordpunct-v1` tokenizer counted 1,235 tokens for the whole payload and 1,150 for the focused payload. Both failed before and passed after one scripted repair turn. This tokenizer counts Unicode word runs and individual punctuation characters; it is **not** an LLM tokenizer, so these numbers are a reproducible context-size proxy, not billed model tokens. The scripted edit measures neither human repair time nor model success rate. This one small case supports no universal token-savings claim.
