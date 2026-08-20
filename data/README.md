# data/

Two things live here, and they are not the same kind of thing.

## The published corpus, and what the pipeline derives from it

`floor_capture_public.jsonl.gz`, `dataset_socle.json`, `snipe_log.json`,
`horizon.json`, `sol_usd_hourly.json` and the `v0*.json` series are the inputs
every measurement in `code/` reads. `MANIFEST.json` carries their sizes and
SHA-256. `python3 code/run_all.py --strict` reruns the measurements and fails if
any committed table or JSON moves by a byte.

## The trace directories, which are an archive

`trace_cohorte/`, `trace_gradues/`, `trace_h2w6/`, `trace_optimus/`,
`trace_polmrkt/`, `trace_temoins/`, `trace_origine_hub/` hold the exploration
that came before the pipeline: one directory per cohort investigated, each with
the scripts that were run and the JSON they produced, side by side.

They are kept because the outputs in `docs/` rest on them and a reader should be
able to see how a number was first arrived at, not only how it is recomputed now.

**The scripts repeat each other, and that is on purpose.** Six directories carry
a step-1 script, six a step-2, six a step-3, and their bodies are identical up to
the mint addresses, the labels and the file names they hold. Factoring them into
one shared module would be the obvious tidy-up, and it is the wrong move here:

- nothing re-runs them. They are frozen next to the outputs they produced, and
  no gate would notice if a refactor changed what they do;
- the correspondence between one script and one directory of results is the
  thing being archived. A shared module dated later than the JSON beside it
  would document a run that never happened;
- the differences are small but real. `trace_temoins/t1_premiers_acheteurs.py`
  is not `trace_cohorte/t1_premiers_acheteurs.py` with a new constant, and
  deciding which variant becomes the shared one is a decision about the past.

Measured over the 66 scripts here, so the claim is checkable. Twelve files fall
into four byte-for-byte identical groups, which is eight redundant copies.
Neutralise the string literals and it grows to seven groups covering 29 files,
so twenty-two redundant copies: three groups of six (the step-1, step-2 and
step-3 scripts), one of four and one of two for `lib_trace.py`, one of three and
one of two.

The 66 scripts of `code/` have none of either, at any depth: the shared logic
there lives in `statlib.py`, `splitlib.py`, `rpc_client.py` and `pumplib.py`.

## What is not committed

`cache/`, `cache_r1/` and the `cache_sigs*/` directories are byte-for-byte
mirrors of public chain data, several hundred megabytes, and worthless in a
clone since any script re-fetches what it needs. Everything derived from them is
committed. See `.gitignore`, which states the reason for each exclusion.
