# Working modes

Pick a mode in the center column, set its options, and start the run below the network view. Every mode uses the same run lifecycle. Each run therefore gets the same worker isolation, live events, records and export.

| Mode | ACT entry | Possible verdicts |
| --- | --- | --- |
| [Fuzzing](#fuzzing) | ACTFuzzer | `falsified` or `unknown` |
| [Verification](#verification) | `verify_once` with interval, dual or HybridZ | ACT's verdict |
| [BaB](#bab) | `verify_bab_batched` | ACT's verdict |

---

## Fuzzing

Fuzzing searches for inputs that violate the specification. It cannot prove that none exist.

- **Options.** Every ACTFuzzer setting appears with ACT's default, and you can edit any of them. The perturbation mode is **isotropic**, **anisotropic** or **fixed**.
- **Batches.** On a shared model, set a batch size to fuzz several input rows in one run, or pick specific inputs.
- **Live view.** For image models, the original, mutated and difference images update while the fuzzer runs, alongside its progress and coverage.
- **Run control.** When the active engine supports it, you can pause, resume or stop a running fuzz, or change its settings. ACT reports whether it applied or rejected each change, and the run record keeps every decision.
- **Counterexamples.** Each violation ACT accepts is saved with the run. It exports as a VNN-LIB assignment or a PNG image.

---

## Verification

Runs ACT's single-pass verification with the abstract domain you choose: **interval**, **dual** or **HybridZ**.

- **Verdict.** The banner shows ACT's own result.
- **Counterexample.** A `falsified` run saves ACT's counterexample, which you can export as a VNN-COMP witness or an image.
- **Diagnostics.** Every run that reaches a worker records warnings, ACT's printed errors, and the exception chain, located at the innermost ACT frame. Run History shows them and offers a reproduction snapshot: a zip with the request, the ACT net, engine information and a `reproduce.py`.

---

## BaB

Runs ACT's batched branch-and-bound, the same entry point as ACT's pipeline command line.

- **Final summary.** The BaB tab shows ACT's final summary and which observation data the run has.
- **Not yet available.** The search tree, node history and node controls need committed node events from ACT, which the pinned engine does not yet provide. The workbench does not reconstruct a tree on its own.

---

## Layer analysis

After a run, step through the interval bounds ACT recorded at each layer.

- Compare a layer's bounds before and after it, and select individual values.
- Project a two-coordinate interval box.
- The view displays recorded data only. It never recomputes bounds in the browser.

---

## Assistant

Ask about the current selection, such as a model, a run, a layer or a value. The assistant freezes that context, collects typed evidence through the same services the views use, and answers with citations you can click to jump to the cited object.

The current provider is a deterministic placeholder. No real language model is connected yet.

---

## Records and export

Every run keeps:

- an immutable **manifest** with the request and engine snapshot;
- an append-only **event log**, which is replayed when the browser reconnects;
- **sealed artifacts**, each checked against its sha256 hash on every read.

The **Records** tab shows provenance and hashes. **Export** downloads the whole record as a zip without absolute server paths.

Next: [Configuration](./configuration).
