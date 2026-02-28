Status: draft

# Add Docstrings

## Summary

Add docstrings to the project's public API once the interfaces have
stabilized. The project deliberately deferred docstrings during early
development to avoid documenting moving targets.

## Acceptance Criteria

- [ ] Identify which modules and classes have stable interfaces ready
      for documentation
- [ ] Add docstrings to stable public APIs (module, class, and
      function level)
- [ ] Verify docstrings follow the project's Python conventions

## Out of Scope

Modifications not directly related to the functionality requested in
this issue are strictly forbidden. Do not refactor adjacent code, update
unrelated files, or extend scope beyond what is specified here.

- Code logic changes
- API refactoring
- Docstrings for internal/private methods unless they are particularly
  non-obvious

## Design Decisions

## Open Questions

- Which subsystems have stable enough interfaces to document now?
- What docstring format should be used? (Google style, NumPy style,
  reStructuredText?)
