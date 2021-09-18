#!/usr/bin/python3

# Simple gitignore cleaner
# You can now mindlessly copy+paste from templates to your heart's desire!

import sys

def isComment(line: str) -> bool: 
	return line.strip().startswith('#')

def withNewLine(line: str) -> str: 
	return line.strip() + '\r\n'


def main():
	if len(sys.argv) > 1:
		gitignore = sys.argv[1]
	else:
		gitignore = '.gitignore'
	
	lines = []
	with open(gitignore, 'rt') as f:
		prevLines = ['']

		for line in f:
			line = line.strip()

			# Skip repeating lines (usually gaps created by other skips)
			if line == prevLines[0]:
				continue

			# Skip obviously redundant lines
			if len(line) and isComment(line) == False and withNewLine(line) in lines:
				continue

			# Skip comments made reduntant by deletions
			if isComment(line):
				hasHitGap = False
				hasHitComment = False
				for prevLine in prevLines:
					if not len(prevLine):
						hasHitGap = True
					elif hasHitGap and len(prevLine):
						hasHitComment = isComment(prevLine)
						break
				if hasHitComment:
					continue

			lines.append(withNewLine(line))
			prevLines.insert(0, line)

	with open(gitignore, 'wt') as f:
		f.writelines(lines)

if __name__ == '__main__':
	main()
