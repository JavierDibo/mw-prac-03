import argparse
import os

def create_sample_log(source_path, output_path, num_lines):
    """
    Reads the first num_lines from the source_path and writes them to output_path.
    """
    print(f"Reading first {num_lines} lines from {source_path}...")
    lines_written = 0
    try:
        with open(source_path, 'r', encoding='utf-8', errors='ignore') as source_file, \
             open(output_path, 'w', encoding='utf-8') as output_file:
            for i, line in enumerate(source_file):
                if i >= num_lines:
                    break
                output_file.write(line)
                lines_written += 1
        print(f"Successfully wrote {lines_written} lines to {output_path}")
    except FileNotFoundError:
        print(f"Error: Source file {source_path} not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a sample log file from a larger log file.")
    parser.add_argument("--source", 
                        default="../datos/NASA_access_log_FULL.txt", 
                        help="Path to the source log file (relative to this script, or absolute).")
    parser.add_argument("--output", 
                        default="sample_first_2000_lines.txt", 
                        help="Path to save the sample log file (in the same directory as this script).")
    parser.add_argument("--lines", 
                        type=int, 
                        default=2000, 
                        help="Number of lines to include in the sample.")

    args = parser.parse_args()

    # Get the absolute directory of the script itself
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Resolve output_path: if relative, join with script_dir; otherwise, use as is.
    output_file_name = args.output
    if not os.path.isabs(output_file_name):
        resolved_output_path = os.path.join(script_dir, output_file_name)
    else:
        resolved_output_path = output_file_name
    
    # Resolve source_path: if relative, join with script_dir and normalize; otherwise, use as is.
    source_file_arg = args.source
    if not os.path.isabs(source_file_arg):
        resolved_source_path = os.path.join(script_dir, source_file_arg)
        resolved_source_path = os.path.normpath(resolved_source_path) # Normalize ../ etc.
    else:
        resolved_source_path = source_file_arg

    create_sample_log(resolved_source_path, resolved_output_path, args.lines) 