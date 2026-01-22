CS5205 – Advanced Artificial Intelligence Lab
Assignment 1
State-Space Scheduling Problem

1. Problem Description

This program solves the assignment scheduling problem using the
STATE-SPACE PARADIGM from Classical Artificial Intelligence.

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
python3 main.py input1.txt 3


5. Output

- Total number of valid schedules
- Each schedule shows:
    Day → Student → Assignment

