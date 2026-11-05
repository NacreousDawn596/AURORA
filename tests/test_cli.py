from aurora.cli import main


def test_cli_runs(capsys) -> None:
    assert main() == 0
    output = capsys.readouterr().out
    assert "illustrative greedy scheduling baseline" in output
    assert "Selected:" in output
