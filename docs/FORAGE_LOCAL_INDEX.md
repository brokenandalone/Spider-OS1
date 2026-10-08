# Forage selected-source local index

The local search backend now uses a separate rebuildable `local-index.sqlite` database. The old `forage.db` is left intact, but its broad legacy index is not used by the new local-search API. Original files are never rewritten. Web search and Deep Forage network synthesis are unchanged.

Copy `forage/config/index.example.json` to `~/.config/spider-os/forage-index.json` and explicitly choose project folders in `roots`. The shipped list is empty. There is no automatic Documents/Downloads/home scan. An empty configured list disables local search and makes a default rebuild request fail with guidance. Explicit `LocalIndex.rebuild([])` clears the derived index without deleting sources.

The existing Forage Index button uses configured roots. A CLI is also available:

```bash
python3 forage/local_index.py rebuild --root /path/to/selected/project
python3 forage/local_index.py search 'search terms'
```

On a selected-module deployment, use the script under `/usr/local/lib/spider-os/forage`. Explicit CLI/API root selection is recorded in that index; subsequent searches use it. Configured selection changes revoke results immediately, before rebuilding. Do not mix explicit indexing with an expectation that the configuration controls consent; rebuild without `--root` to switch back to configured selection.

Indexing supports bounded UTF-8 text/source files. It excludes hidden paths, common credential names, symlinks, binary and oversized files. This is not a secret detector: review selected project content for embedded private data. DOCX/PDF/audio extraction and application-entry indexing are not implemented in this batch.

Results provide an original-file URI, selected root, indexed content SHA-256 and index timestamp. Freshness checks compare current file size/mtime with the indexed version; this is not a cryptographic check of live file content. Changed sources are labeled stale in the existing result display, and removed or symlink-retargeted sources are omitted. Results still show the indexed text until a successful rebuild.

Rebuild creates a private staging database, checks integrity and replaces the published database atomically. Failure preserves the previous usable index. A successful rebuild drops deleted files and unselected roots. Overlapping roots and whole-home/filesystem selection are rejected. Indexing does not send data to Ollama or any web/cloud service.

Source regression tests cover selected-source provenance, Unicode queries, changed/deleted files, credentials/binary/size exclusions, symlinks, interrupted rebuilds, consent revocation, safe search syntax and full reconstruction after index loss. Local search remains separate from the planned Threads, Timeline and research queue. Installed source selection and actual source-link opening still require PC qualification.
