#!/usr/bin/env python3
"""
Entry point script for Apify that:
1. Runs the country normalization fix script
2. Then runs the main normalization process
"""
import os
import sys
import logging
import subprocess
import argparse
import time
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("apify_entry.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_with_timeout(cmd, timeout_seconds=1800):  # Default 30-minute timeout
    """
    Run a command with a timeout.
    
    Args:
        cmd: Command to run as a list of strings
        timeout_seconds: Timeout in seconds
        
    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    start_time = time.time()
    
    # Start the process
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Initialize output buffers
    stdout_chunks = []
    stderr_chunks = []
    
    # Set up non-blocking reading
    import select
    # Get file descriptors for stdout and stderr
    stdout_fd = process.stdout.fileno()
    stderr_fd = process.stderr.fileno()
    
    # Monitor for output while process is running
    while process.poll() is None:
        # Check if we've exceeded the timeout
        if time.time() - start_time > timeout_seconds:
            logger.warning(f"Process timed out after {timeout_seconds} seconds. Terminating...")
            process.terminate()
            try:
                # Give it a chance to terminate gracefully
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
            
            # Get any remaining output
            stdout, stderr = process.communicate()
            stdout_chunks.append(stdout if stdout else "")
            stderr_chunks.append(stderr if stderr else "")
            
            return (
                -1,  # -1 indicates timeout
                "".join(stdout_chunks),
                "".join(stderr_chunks) + f"\nProcess timed out after {timeout_seconds} seconds"
            )
        
        # Check for output without blocking (wait up to 1 second)
        ready_fds, _, _ = select.select([stdout_fd, stderr_fd], [], [], 1)
        
        # Read from stdout if it's ready
        if stdout_fd in ready_fds:
            output = process.stdout.readline()
            if output:
                stdout_chunks.append(output)
                # Log every 10th line to show progress
                if len(stdout_chunks) % 10 == 0:
                    logger.info(f"Process running, {len(stdout_chunks)} lines of output so far...")
                    # Also log the latest line for context
                    logger.info(f"Latest output: {output.strip()}")
        
        # Read from stderr if it's ready
        if stderr_fd in ready_fds:
            error = process.stderr.readline()
            if error:
                stderr_chunks.append(error)
                # Log all stderr lines as they often indicate issues
                logger.warning(f"Process stderr: {error.strip()}")
    
    # Process has completed, get any remaining output
    stdout, stderr = process.communicate()
    stdout_chunks.append(stdout if stdout else "")
    stderr_chunks.append(stderr if stderr else "")
    
    return (
        process.returncode,
        "".join(stdout_chunks),
        "".join(stderr_chunks)
    )

def main():
    """
    Main entry point that runs both scripts in sequence.
    """
    script_name = os.path.basename(__file__)
    logger.info(f"Starting {script_name}")
    
    # Parse command-line arguments to pass through to apify_normalize.py
    parser = argparse.ArgumentParser(description="Run country fix and normalization on Apify")
    parser.add_argument("--test", action="store_true", help="Run in test mode (process fewer records)")
    parser.add_argument("--tables", type=str, nargs="*", help="Specific tables to process")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    parser.add_argument("--limit", type=int, help="Maximum number of records to process per table")
    parser.add_argument("--skip-fix", action="store_true", help="Skip the country normalization fix")
    parser.add_argument("--timeout", type=int, default=1800, help="Timeout in seconds (default: 1800 = 30 minutes)")
    args = parser.parse_args()
    
    try:
        # Check if Supabase environment variables are set
        if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
            logger.error("Supabase environment variables not set. Please set SUPABASE_URL and SUPABASE_KEY.")
            sys.exit(1)
        
        # 1. Run country normalization fix first (unless skipped)
        if not args.skip_fix:
            logger.info("Running country normalization fix...")
            fix_cmd = ["python", "fix_country_normalization.py", "--batch-size", str(args.batch_size or 100)]
            
            # Run the country fix with a shorter timeout (5 minutes)
            fix_code, fix_stdout, fix_stderr = run_with_timeout(fix_cmd, timeout_seconds=300)
            
            logger.info(f"Country fix exit code: {fix_code}")
            logger.info(f"Country fix output:\n{fix_stdout}")
            if fix_stderr:
                logger.warning(f"Country fix stderr:\n{fix_stderr}")
                
            # If the country fix failed or timed out, log warning but continue
            if fix_code != 0:
                logger.warning("Country fix did not complete successfully, but continuing with main normalization")
        else:
            logger.info("Skipping country normalization fix as requested")
        
        # 2. Run main normalization process
        logger.info("Running main normalization process...")
        
        # Build command for apify_normalize.py with all relevant arguments
        normalize_cmd = ["python", "apify_normalize.py"]
        if args.test:
            normalize_cmd.append("--test")
        if args.tables:
            normalize_cmd.extend(["--tables"] + args.tables)
        if args.batch_size:
            normalize_cmd.extend(["--batch-size", str(args.batch_size)])
        if args.limit:
            normalize_cmd.extend(["--limit", str(args.limit)])
        
        # Run the normalization process with the specified timeout
        logger.info(f"Starting main normalization with a timeout of {args.timeout} seconds...")
        norm_code, norm_stdout, norm_stderr = run_with_timeout(normalize_cmd, timeout_seconds=args.timeout)
        
        # Handle different outcomes
        if norm_code == 0:
            logger.info("Normalization completed successfully")
            logger.info(f"Normalization output:\n{norm_stdout}")
            if norm_stderr:
                logger.warning(f"Normalization stderr:\n{norm_stderr}")
        elif norm_code == -1:
            logger.error(f"Normalization TIMED OUT after {args.timeout} seconds")
            logger.info(f"Partial output:\n{norm_stdout}")
            logger.error(f"Error output:\n{norm_stderr}")
            sys.exit(2)  # Exit with code 2 for timeout
        else:
            logger.error(f"Normalization FAILED with exit code {norm_code}")
            logger.info(f"Output before failure:\n{norm_stdout}")
            logger.error(f"Error output:\n{norm_stderr}")
            sys.exit(norm_code)
            
        logger.info("Both processes completed")
        
    except Exception as e:
        logger.exception(f"Error in entry script: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 