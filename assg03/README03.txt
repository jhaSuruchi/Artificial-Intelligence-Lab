How to execute:-

Query 1: Find earliest completion with given subscription


python3 assg03.py <file> <case> <N> 1 <gpt-limit> <gem-limit>

Examples:
  python3 assg03.py input.txt A 3 1 5 5
  python3 assg03.py input.txt B 2 1 10 8

Output: Compares DFS, DFBB, and A* algorithms showing:
  - Minimum days needed
  - Nodes expanded (efficiency metric)
  - Complete schedule


Query 2: Find optimal subscription within deadline


python3 assg03.py <file> <case> <N> 2 <deadline> <c1> <c2>

Examples:
  python3 assg03.py test_input.txt A 3 2 8 2 3
  python3 assg03.py test_input.txt B 3 2 5 10 15

Output:
  - Optimal subscription (ChatGPT and Gemini prompts per day)
  - Minimum daily cost
  - Schedule achieving the deadline