#!/usr/bin/env python
"""
Run Pantheon Evolution on the TopACT Algorithm.

Optimizes TopACT spatial transcriptomics annotation for speed
while maintaining fidelity to the original output.

Usage:
    python run_evolution.py [--iterations N] [--output DIR]

Example:
    python run_evolution.py --iterations 50 --output results/
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env file from the example directory
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # dotenv not required if env vars are set directly

# Set TOPACT_DATA_DIR so evaluator can find data when running in temp workspace
_example_dir = Path(__file__).parent.resolve()
os.environ.setdefault("TOPACT_DATA_DIR", str(_example_dir / "data"))


async def run_evolution(
    iterations: int = 50,
    output_dir: str = None,
    verbose: bool = False,
    resume: str = None,
):
    """
    Run the evolution process on TopACT.

    Args:
        iterations: Maximum number of evolution iterations
        output_dir: Directory to save results
        verbose: Enable verbose logging
        resume: Path to resume evolution from
    """
    from pantheon.evolution import EvolutionTeam, EvolutionConfig
    from pantheon.evolution.program import CodebaseSnapshot

    # Get paths
    example_dir = Path(__file__).parent
    topact_dir = example_dir / "topact"
    evaluator_path = example_dir / "evaluator.py"

    # Load initial code: all .py files under topact/, keyed as "topact/<name>.py"
    files = {}
    for py_file in sorted(topact_dir.glob("*.py")):
        rel_path = f"topact/{py_file.name}"
        files[rel_path] = py_file.read_text()
    initial_code = CodebaseSnapshot(files=files)

    # Load evaluator code
    evaluator_code = evaluator_path.read_text()

    # Load or create configuration
    config_path = Path(output_dir) / "config.yaml" if output_dir else None
    if config_path and config_path.exists():
        config = EvolutionConfig.from_yaml(str(config_path))
        config.max_iterations = iterations
        config.log_level = "DEBUG" if verbose else "INFO"
        print(f"Loaded config from: {config_path}")
    else:
        config = EvolutionConfig(
            max_iterations=iterations,
            num_workers=4,
            num_islands=2,
            num_inspirations=2,
            num_top_programs=3,
            max_parallel_evaluations=2,
            evaluation_timeout=300,  # TopACT pipeline can be slow
            analyzer_timeout=120,
            feature_dimensions=["speed_score", "fidelity_score"],
            early_stop_generations=200,
            function_weight=1.0,
            llm_weight=0.0,
            log_level="DEBUG" if verbose else "INFO",
            log_iterations=True,
            checkpoint_interval=10,
            db_path=output_dir,
        )

    # Define optimization objective
    objective = """Optimize the TopACT spatial transcriptomics annotation implementation for:

1. **Speed** (40% weight): Reduce execution time of the full pipeline.
   - Optimize matrix operations and avoid redundant computations
   - Consider vectorization opportunities in numpy/scipy operations
   - Improve the efficiency of spatial grid construction and neighborhood aggregation
   - Optimize the multiscale classification loop

2. **Fidelity** (60% weight): Maintain output consistency with the original implementation.
   - The annotation output must match the reference output
   - Fidelity below 90% is unacceptable (score drops to 0)
   - Preserve the mathematical correctness of all operations

Constraints:
- Keep the public API (CountMatrix, SVCClassifier, CountGrid, etc.)
- Maintain the same classification pipeline structure
- Don't remove essential functionality
- Don't change the output format
"""

    print("=" * 60)
    print("Pantheon Evolution: TopACT Optimization")
    print("=" * 60)
    print(f"\nInitial code: {topact_dir} ({initial_code.file_count()} files, {initial_code.total_lines()} lines)")
    print(f"Evaluator: {evaluator_path}")
    print(f"Iterations: {iterations}")
    print(f"Output: {output_dir or 'None (results not saved)'}")
    if resume:
        print(f"Resume from: {resume}")
    print("\n" + "-" * 60)
    print("Starting evolution...\n")

    # Create and run evolution team
    team = EvolutionTeam(config=config)
    result = await team.evolve(
        initial_code=initial_code,
        evaluator_code=evaluator_code,
        objective=objective,
        resume_from=resume,
    )

    # Print results
    print("\n" + "=" * 60)
    print(result.get_summary())

    # Save results if output specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save best code (multi-file)
        if result.best_program:
            best_code_dir = output_path / "topact_optimized"
            best_code_dir.mkdir(parents=True, exist_ok=True)
            for file_path, content in result.best_program.snapshot.files.items():
                full_path = best_code_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
            print(f"\nBest code saved to: {best_code_dir}")

        # Save report
        report_path = output_path / "evolution_report.json"
        result.save_report(str(report_path))
        print(f"Report saved to: {report_path}")

        # Save configuration
        config.to_yaml(str(output_path / "config.yaml"))

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Evolve TopACT using Pantheon Evolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick test run
  python run_evolution.py --iterations 10

  # Full evolution with output
  python run_evolution.py --iterations 100 --output results/

  # Verbose mode
  python run_evolution.py --iterations 50 --verbose

  # Resume from checkpoint
  python run_evolution.py --iterations 100 --output results/ --resume results/
        """,
    )

    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=50,
        help="Maximum number of evolution iterations (default: 50)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output directory for results",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--resume", "-r",
        type=str,
        default=None,
        help="Resume evolution from checkpoint directory",
    )

    args = parser.parse_args()

    try:
        result = asyncio.run(run_evolution(
            iterations=args.iterations,
            output_dir=args.output,
            verbose=args.verbose,
            resume=args.resume,
        ))
        print(f"\nFinal best score: {result.best_score:.4f}")
    except KeyboardInterrupt:
        print("\nEvolution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
