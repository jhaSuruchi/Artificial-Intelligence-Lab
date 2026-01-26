Assignment 1
State-Space Scheduling Problem


Given:
- N students
- K prompts per student per day
- A set of assignments
- Each assignment has:
    • Required number of prompts
    • A list of dependency assignments
- An assignment must be completed by exactly one student
- No partial completion is allowed
- Students cannot share prompts
- Multiple assignments per student per day are allowed
- All assignments must be completed within M days

The program prints ALL POSSIBLE VALID SCHEDULES.

1. My assumptions

- Sutdents are different entities 
    • Like S1 doing A1 is different then S2 doing A2
- Slacking is allowed
    • Move to next day even if student have sufficient prompts.

2. State-Space Formulation


State = (CompletedAssignments, CurrentDay, PromptUsagePerStudent)

Initial State:
- CompletedAssignments = empty set
- CurrentDay = 1
- PromptUsagePerStudent = [0, 0, ..., 0]

Goal State:
- All assignments completed within M days

Operators:
- Assign an assignment to a student on the current day if:
    • All dependencies are completed
    • Student has enough remaining prompts

Search Strategy:
- Depth First Search (DFS) with backtracking
- Exhaustively enumerates all valid schedules


3. How to Run


Requirements:
- Python 3.x

Command:
python3 main.py <input-file> <number-of-days>

Example:
python3 assg01.py input01.txt 3


5. Output

- Each schedule shows:
    Day -> Student -> Assignment
- Total number of valid schedules


6. Complexity

    • A = number of assignments
    • N = students
    • m = maximum allowed days
    • Slack days = m − 1 (worst case)

- Time Complexity:
    - b <= (A × N + 1)
    - d <= (A + m)
    • Worst case Time Complexity = O(b^d)

- Space Complexity:
    - d <= (A + m)
    • Worst case Time Complexity = O(d) = O(A+m)