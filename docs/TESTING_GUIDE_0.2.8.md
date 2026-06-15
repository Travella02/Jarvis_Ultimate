# Testing Guide - 0.2.8 Memory Pipeline Foundation

## 1. Run the full test suite

From the project root:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 2. Launch Jarvis

```powershell
python scripts\start_jarvis_app.py
```

## 3. Test saving memory

Say or type:

```text
Jarvis, remember that my favorite test color is blue
```

Expected:

```text
I’ll remember that, sir.
```

## 4. Test searching memory

Say or type:

```text
Jarvis, what do you remember about my favorite test color?
```

Expected: Jarvis should mention the saved blue/test color memory.

## 5. Test memory status

Say or type:

```text
Jarvis, memory status
```

Expected: Jarvis should report short-term and long-term memory status.

## 6. Test forgetting memory

Say or type:

```text
Jarvis, forget the memory about favorite test color
```

Expected: Jarvis should confirm he forgot the matching memory.

Then ask again:

```text
Jarvis, what do you remember about favorite test color?
```

Expected: Jarvis should say he does not have a matching saved memory.

## 7. Check the local memory file

After saving a memory, this file should exist:

```text
data/memory/long_term_memory.json
```

This is the local long-term memory store for now.

## Notes
- Jarvis should not save random conversation automatically yet.
- Jarvis should only save durable memory when explicitly asked.
- Long-term memory is separate from short-term conversation memory.
