#!/usr/bin/python3

# Simple gitignore cleaner
# You can now mindlessly copy+paste from templates to your heart's desire!

import sys
import re

comment = re.compile('#+ .+')
has_content = lambda line: bool(len(line)) and not comment.fullmatch(line)

GITIGNORE_PATH = '.gitignore'

def main():
	lines = []
	with open(GITIGNORE_PATH, 'rt') as f:
		for line in f:
			line = line.strip()
			# Skip repeating lines (usually gaps created by other skips)
			if len(lines) and line == lines[-1]:
				continue

			# Skip obviously redundant lines
			if has_content(line) and line in lines:
				strip_end = 0
				# Trim other lines (comments) made irrevelant by skip
				for i, prev_line in enumerate(reversed(lines)):
					if has_content(prev_line):
						break
					strip_end = i
				if strip_end:
					lines = lines[: -strip_end]
				continue

			lines.append(line)

	with open(GITIGNORE_PATH, 'wt') as f:
		f.writelines([line + '\r\n' for line in lines])

if __name__ == '__main__':
	if len(sys.argv) > 1:
		GITIGNORE_PATH = sys.argv[1]
	main()
