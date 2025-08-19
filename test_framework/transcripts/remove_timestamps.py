import os
from pathlib import Path

def clean_transcript(text):
    """
    Removes timestamp patterns and asterisk prefixes by reading character by character.
    No regex used anywhere.
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        # Remove * prefix if present
        if line.startswith('* '):
            line = line[2:]
        
        # Clean the line character by character
        cleaned_line = clean_line_char_by_char(line)
        if cleaned_line.strip():
            cleaned_lines.append(cleaned_line.strip())
    
    return '\n'.join(cleaned_lines)

def clean_line_char_by_char(line):
    """
    Read character by character, skip timestamp patterns.
    """
    result = []
    i = 0
    
    while i < len(line):
        # Check for M:SS pattern (single digit minute)
        if (i <= len(line) - 4 and
            line[i].isdigit() and 
            line[i + 1] == ':' and 
            line[i + 2].isdigit() and 
            line[i + 3].isdigit()):
            # Skip the M:SS pattern
            i += 4
            continue
        
        # Check for MM:SS pattern (double digit minute)
        if (i <= len(line) - 5 and
            line[i].isdigit() and 
            line[i + 1].isdigit() and 
            line[i + 2] == ':' and 
            line[i + 3].isdigit() and 
            line[i + 4].isdigit()):
            # Skip the MM:SS pattern
            i += 5
            continue
        
        # Keep this character
        result.append(line[i])
        i += 1
    
    return ''.join(result)

def process_all_transcripts():
    """
    Process all transcript files in both '5min_transcripts' and '30min_transcripts'
    inside original_transcripts, saving cleaned versions to the corresponding
    subfolders in edited_transcripts. Also processes any .txt files at the root
    of original_transcripts and saves to the root of edited_transcripts.
    """
    # Resolve base folder paths relative to this script file
    base_dir = Path(__file__).parent
    original_base = base_dir / 'original_transcripts'
    edited_base = base_dir / 'edited_transcripts'

    # Ensure edited base exists
    edited_base.mkdir(exist_ok=True)

    # Check if original_transcripts folder exists
    if not original_base.exists():
        print(f"Error: {original_base} folder not found!")
        print("Please create the folder and add your transcript files.")
        return

    def process_folder(original_folder: Path, edited_folder: Path) -> int:
        """Process all .txt files from original_folder into edited_folder."""
        processed_count = 0
        # Create edited subfolder if needed
        edited_folder.mkdir(parents=True, exist_ok=True)

        # Gather .txt files if the original subfolder exists
        if not original_folder.exists():
            return 0
        transcript_files = list(original_folder.glob('*.txt'))
        if not transcript_files:
            return 0

        for file_path in transcript_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    transcript_text = file.read()
                cleaned_text = clean_transcript(transcript_text)

                output_path = edited_folder / file_path.name
                with open(output_path, 'w', encoding='utf-8') as file:
                    file.write(cleaned_text)

                print(f"✓ Processed: {file_path.name} -> {edited_folder.relative_to(base_dir)}")
                processed_count += 1
            except Exception as e:
                print(f"✗ Error processing {file_path.name}: {e}")
        return processed_count

    total_processed = 0

    # 1) Root-level files (if any)
    total_processed += process_folder(original_base, edited_base)

    # 2) 5-minute transcripts
    total_processed += process_folder(
        original_base / '5min_transcripts',
        edited_base / '5min_transcripts'
    )

    # 3) 30-minute transcripts
    total_processed += process_folder(
        original_base / '30min_transcripts',
        edited_base / '30min_transcripts'
    )

    print(f"\nCompleted! Processed {total_processed} transcript(s).")
    print(f"Cleaned files saved in '{edited_base.relative_to(base_dir)}' and subfolders.")

if __name__ == "__main__":
    process_all_transcripts()