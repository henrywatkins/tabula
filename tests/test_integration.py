"""Integration tests for the statx CLI."""

import io
import tempfile
from click.testing import CliRunner
from statx.cli import statx


def test_ols_with_csv_file():
    """Test OLS regression with a CSV file."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv") as f:
        # Write test data
        f.write("x,y,group\n")
        f.write("1,3.4,A\n")
        f.write("2,5.7,A\n")
        f.write("3,6.3,B\n")
        f.write("4,8.1,B\n")
        f.flush()

        # Run the command
        result = runner.invoke(
            statx, [f.name, "-p", "test:ols,dependent:y,independent:x"]
        )

        # Check the output
        assert result.exit_code == 0
        assert "OLS Regression Results" in result.output
        assert "R-squared:" in result.output
        assert "x" in result.output


def test_ttest_with_stdin():
    """Test t-test with stdin data."""
    runner = CliRunner()
    data = "x,y,group\n1,3.4,A\n2,5.7,A\n3,6.3,B\n4,8.1,B\n"

    result = runner.invoke(statx, ["-p", "test:ttest,sample1:x,sample2:y"], input=data)

    assert result.exit_code == 0
    assert "t-statistic:" in result.output
    assert "p-value:" in result.output


def test_output_to_file():
    """Test saving output to a file."""
    runner = CliRunner()
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv") as input_file:
        # Write test data
        input_file.write("x,y,group\n")
        input_file.write("1,3.4,A\n")
        input_file.write("2,5.7,A\n")
        input_file.write("3,6.3,B\n")
        input_file.write("4,8.1,B\n")
        input_file.flush()

        with tempfile.NamedTemporaryFile(mode="w+") as output_file:
            # Run the command
            result = runner.invoke(
                statx,
                [
                    input_file.name,
                    "-p",
                    "test:ols,dependent:y,independent:x",
                    "-o",
                    output_file.name,
                ],
            )

            # Check command output
            assert result.exit_code == 0
            assert f"Test result saved to {output_file.name}" in result.output

            # Check file content
            output_file.seek(0)
            content = output_file.read()
            assert "OLS Regression Results" in content
            assert "R-squared:" in content


def test_custom_separator():
    """Test using a custom separator."""
    runner = CliRunner()
    data = "x;y;group\n1;3.4;A\n2;5.7;A\n3;6.3;B\n4;8.1;B\n"

    result = runner.invoke(
        statx, ["-p", "test:ols,dependent:y,independent:x", "-s", ";"], input=data
    )

    assert result.exit_code == 0
    assert "OLS Regression Results" in result.output


def test_custom_column_names():
    """Test providing custom column names."""
    runner = CliRunner()
    # Data without headers
    data = "1,3.4,A\n2,5.7,A\n3,6.3,B\n4,8.1,B\n"

    result = runner.invoke(
        statx,
        ["-p", "test:ols,dependent:y,independent:x", "-c", "x,y,group"],
        input=data,
    )

    assert result.exit_code == 0
    assert "OLS Regression Results" in result.output


def test_glm_with_poisson_family():
    """Test GLM with Poisson family."""
    runner = CliRunner()
    # Create data with count variable
    data = "x,count,group\n1,2,A\n2,4,A\n3,7,B\n4,12,B\n"

    result = runner.invoke(
        statx,
        ["-p", "test:glm,dependent:count,independent:x,family:poisson"],
        input=data,
    )

    assert result.exit_code == 0
    assert "Generalized Linear Model Regression Results" in result.output
    assert "Poisson" in result.output


def test_glm_with_custom_link():
    """Test GLM with custom link function."""
    runner = CliRunner()
    data = "x,y,group\n1,3.4,A\n2,5.7,A\n3,6.3,B\n4,8.1,B\n"

    result = runner.invoke(
        statx,
        ["-p", "test:glm,dependent:y,independent:x,family:gaussian,link:log"],
        input=data,
    )

    assert result.exit_code == 0
    assert "Generalized Linear Model Regression Results" in result.output
    assert "Gaussian" in result.output
    assert "Log" in result.output
