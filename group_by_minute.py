import re
import sys


def parse_and_group_by_minute(input_file: str, output_file: str):
    """Group transcript lines into 1-minute paragraphs."""
    pattern = r'\[([\d.]+)s\]\s+(.+)'

    # Parse all lines with timestamps
    entries = []
    with open(input_file, 'r') as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                timestamp = float(match.group(1))
                text = match.group(2).strip()
                entries.append((timestamp, text))

    if not entries:
        print("No transcript entries found")
        return

    # Group by minute
    minutes = {}
    for timestamp, text in entries:
        minute = int(timestamp // 60)
        if minute not in minutes:
            minutes[minute] = []
        minutes[minute].append(text)

    # Write grouped output
    with open(output_file, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("TRANSCRIPT (Grouped by Minute)\n")
        f.write("=" * 60 + "\n\n")

        for minute in sorted(minutes.keys()):
            # Format time as MM:SS range
            start_time = f"{minute}:00"
            end_time = f"{minute}:59"

            f.write(f"[{start_time} - {end_time}]\n")
            f.write("-" * 40 + "\n")

            # Join all text for this minute into a paragraph
            paragraph = " ".join(minutes[minute])

            # Word wrap at ~80 characters
            words = paragraph.split()
            lines = []
            current_line = []
            current_length = 0

            for word in words:
                if current_length + len(word) + 1 > 80:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    current_line.append(word)
                    current_length += len(word) + 1

            if current_line:
                lines.append(" ".join(current_line))

            for line in lines:
                f.write(f"{line}\n")

            f.write("\n")

        f.write("=" * 60 + "\n")
        f.write(f"Total: {len(minutes)} minutes, {len(entries)} lines\n")

    print(f"Grouped transcript saved to: {output_file}")
    print(f"Total: {len(minutes)} minutes, {len(entries)} original lines")


if __name__ == "__main__":
    input_file = "transcript.log"
    output_file = "transcript_by_minute.log"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    parse_and_group_by_minute(input_file, output_file)
