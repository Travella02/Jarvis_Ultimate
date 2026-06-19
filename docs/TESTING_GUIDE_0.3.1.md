# Jarvis Ultimate 0.3.1 Testing Guide — Entity Memory Foundation

## 1. Apply the patch

From the root of your Jarvis Ultimate project, run:

```powershell
python apply_0_3_1_entity_memory_patch.py
```

The installer copies the replacement files into the project and creates `.patch_backups/0.3.1_entity_memory/` before overwriting anything.

## 2. Run the full test suite

From the project root, run:

```powershell
python -m unittest discover -s tests -v
```

If your terminal cannot import `jarvis`, run this instead:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

This patch was validated in the patch workspace with:

```text
Ran 349 tests in 3.366s
OK
```

## 3. Manual memory checks

Start Jarvis normally, then try these commands:

```text
Jarvis, memory status
```

Expected: the response includes short-term memory, long-term memory, chat archive, and `Entity memory status`.

```text
Jarvis, remember that Kenleigh is my fiancée
```

Expected: Jarvis says he will remember it. This saves the normal long-term fact and also creates/updates a structured `person` entity.

```text
Jarvis, who is Kenleigh?
```

Expected: Jarvis answers from structured entity memory and says Kenleigh is remembered as a person / the user's fiancée.

```text
Jarvis, remember that my dog Scout is a golden doodle
```

Expected: Jarvis saves the fact and creates/updates a structured `pet` entity.

```text
Jarvis, list remembered pets
```

Expected: Jarvis lists Scout as a pet entity.

```text
Jarvis, entity memory status
```

Expected: Jarvis reports the entity-memory record count and the registered entity type count.

## 4. SaaS scalability check

This patch supports custom entity types through the registry. The included automated tests validate that a new type like `subscription` can be registered and used without changing the schema.

You do not need to manually edit the entity registry yet. This is foundation work for future SaaS memory categories like workspaces, subscriptions, customers, teams, tickets, or routines.

## 5. Data files to inspect

After saving entity memories, inspect:

```text
data/memory/entities.json
```

Expected: JSON with:

- `schema_version`,
- `entity_types`,
- `records`.

Each record should include fields like:

- `name`,
- `entity_type`,
- `summary`,
- `attributes`,
- `relationships`,
- `tags`,
- `sensitivity`,
- `scope`,
- `metadata`.

## 6. Common issues

### `ModuleNotFoundError: No module named 'jarvis'`

Run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

### Entity search says nothing is saved

Make sure you used an explicit save command first, such as:

```text
Jarvis, remember that Kenleigh is my fiancée
```

Then retry:

```text
Jarvis, who is Kenleigh?
```

### Jarvis does not create an entity for a memory

0.3.1 intentionally uses conservative extraction. If a memory is not recognized as an entity, it will still save as normal long-term memory. Entity extraction can be expanded safely in later updates.

