import importlib

import app.config as config


def test_config_loads_dotenv_from_parent_directory(tmp_path, monkeypatch):
    backend_dir = tmp_path / "backend"
    backend_dir.mkdir()

    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "\n".join(
            [
                "EMAIL_PROVIDER=mailjet",
                "EMAIL_API_KEY=from-dotenv",
                "EMAIL_SECRET_KEY=secret-from-dotenv",
                "EMAIL_FROM=sender@example.com",
                "ALLOWED_ORIGINS=http://localhost:3000",
                "DOWNLOAD_BASE_URL=http://localhost:9000",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(backend_dir)
    monkeypatch.delenv("EMAIL_PROVIDER", raising=False)
    monkeypatch.delenv("EMAIL_API_KEY", raising=False)
    monkeypatch.delenv("EMAIL_SECRET_KEY", raising=False)
    monkeypatch.delenv("EMAIL_FROM", raising=False)
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    monkeypatch.delenv("DOWNLOAD_BASE_URL", raising=False)

    reloaded = importlib.reload(config)

    assert reloaded.EMAIL_PROVIDER == "mailjet"
    assert reloaded.EMAIL_API_KEY == "from-dotenv"
    assert reloaded.EMAIL_SECRET_KEY == "secret-from-dotenv"
    assert reloaded.EMAIL_FROM == "sender@example.com"
    assert reloaded.ALLOWED_ORIGINS == ["http://localhost:3000"]
    assert reloaded.DOWNLOAD_BASE_URL == "http://localhost:9000"
