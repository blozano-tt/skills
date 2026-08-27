# llk-api-contract-review

Reviews tt-llk changes against the LLK API and hardware-state contract — unpack-to-dest bit-width and Math-thread rules, TTI/TT_OP macro class, pool-type clear values, CFG read-after-write ordering, STALLWAIT necessity, missing asserts, WH/BH/QSR parity, metal-side propagation and breaking changes, and the maintainability patterns the team consistently flags. Use when reviewing changes under tt_metal/tt-llk.

**Bucket:** `llk`  
**Source:** [`skills/llk/llk-api-contract-review/SKILL.md`](../../skills/llk/llk-api-contract-review/SKILL.md)

## Pinning

```yaml
skills:
  - blozano-tt/skills/llk-api-contract-review@<sha>
```

Pins resolve by skill name, not path.

## Provenance

Vendored from an unlicensed private upstream under a disclosure gate that is **not yet closed** —
see [ADR-0004](../../.agents/adr/0004-llk-code-gen-vendoring.md) before pinning this skill.

See [SOURCES.md](../../SOURCES.md) for upstream paths and author attribution.
