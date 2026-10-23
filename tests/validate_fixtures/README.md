# Validator fixtures

Two miniature overlay trees for `tests/test_validate.py` (task 1.6). They are not solver
fixtures (those live in `tests/fixtures/<case>/`).

- `good/` passes every `caen validate` rule.
- `broken/` breaks every rule on purpose; each defect is listed in `test_validate.py`.

The French texts and keyword names are copied from upstream 17.4.26
(`code_aster/Messages/catamess.py`, `code_aster/Cata/Commands/affe_modele.py`), trimmed.
The English texts are test data, not translations for use.
