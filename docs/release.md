# Публикация

Проект публикуется как пакет `xmcd` в PyPI и как открытый репозиторий `nickadminroot/xmcd` на GitHub.

Локальная проверка перед релизом:

```bash
uv lock --check
uv run ruff check src tests examples
uv run ruff format --check src tests examples
uv run pytest -q
uv build
uv publish --dry-run dist/*
```

Версия в `pyproject.toml` должна совпадать с новым Git-тегом `v<версия>`. GitHub Actions запускает тесты на каждом push и pull request. Публикация в PyPI выполняется после публикации GitHub Release через Trusted Publishing; для этого в настройках PyPI проекта должен быть добавлен publisher `nickadminroot/xmcd`, workflow `.github/workflows/publish.yml`, environment `pypi` не требуется.

Ручная загрузка из окружения с токеном:

```bash
UV_PUBLISH_TOKEN='pypi-...' uv publish dist/*
```

Токен не добавляется в Git, shell history или сообщения. Номер версии PyPI нельзя переиспользовать после успешной загрузки; перед публикацией проверьте `uv build` и содержимое `dist/`.
