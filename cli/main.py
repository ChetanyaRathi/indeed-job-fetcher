import argparse
import json
import sys
from pathlib import Path
from dataclasses import asdict
from rich.console import Console
from rich.table import Table

from jobfit.engine import pipeline
from jobfit.config import TOP_K, MIN_FIT, EASY_APPLY_ONLY, DATA_DIR

def main():
    parser = argparse.ArgumentParser(description="Indeed Job Fetcher - CLI")
    parser.add_argument("--resume", required=True, help="Path to resume file (PDF or TXT)")
    parser.add_argument("--jobs", required=True, help="Path to folder containing job descriptions")
    parser.add_argument("--top-k", type=int, default=TOP_K, help="How many jobs the LLM judges")
    parser.add_argument("--min-fit", type=int, default=MIN_FIT, help="Minimum fit score (0-100)")
    parser.add_argument("--easy-apply-only", action="store_true", default=EASY_APPLY_ONLY, help="Only show easy apply jobs")
    
    args = parser.parse_args()
    console = Console()
    
    try:
        results = pipeline.run(
            resume_path=args.resume,
            jobs_dir=args.jobs,
            top_k=args.top_k,
            min_fit=args.min_fit,
            easy_apply_only=args.easy_apply_only
        )
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("Make sure your model server is running and models are downloaded.")
        sys.exit(1)
        
    if not results:
        console.print("[yellow]No jobs matched the criteria.[/yellow]")
        sys.exit(0)
        
    # Build Table
    table = Table(title="Job Fit Rankings")
    table.add_column("Rank", justify="right", style="cyan", no_wrap=True)
    table.add_column("Fit%", justify="right", style="green")
    table.add_column("Title", style="magenta")
    table.add_column("Company", style="blue")
    table.add_column("Salary", style="yellow")
    table.add_column("Apply Link", style="blue")
    
    output_dir = Path(DATA_DIR) / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    flattened_results = []
    
    for i, res in enumerate(results, 1):
        salary_str = res.job.salary if res.job.salary else "N/A"
        link_str = res.job.apply_url if res.job.apply_url else "N/A"
        
        table.add_row(
            str(i),
            str(res.fit_score),
            res.job.title,
            res.job.company,
            salary_str,
            link_str
        )
        
        flat = {
            "title": res.job.title,
            "company": res.job.company,
            "location": res.job.location,
            "salary": res.job.salary,
            "apply_url": res.job.apply_url,
            "easy_apply": res.job.easy_apply,
            "fit_score": res.fit_score,
            "matched_skills": res.matched_skills,
            "missing_skills": res.missing_skills,
            "reason": res.reason
        }
        flattened_results.append(flat)
        
    console.print(table)
    
    output_path = output_dir / "results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flattened_results, f, indent=2)
        
    console.print(f"\n[green]Results saved to {output_path}[/green]")

if __name__ == "__main__":
    main()
