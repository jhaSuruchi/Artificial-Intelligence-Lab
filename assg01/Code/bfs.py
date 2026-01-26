import sys
from collections import deque

def parse_input(filename):
    assignments = {}
    dependencies = {}

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue

            parts = line.split()
            if parts[0] == 'N':
                N = int(parts[1])
            elif parts[0] == 'K':
                K = int(parts[1])
            elif parts[0] == 'A':
                aid = f"A{parts[1]}"
                prompts = int(parts[2])
                deps = []
                for d in parts[3:]:
                    if d == '0':
                        break
                    deps.append(f"A{d}")
                assignments[aid] = prompts
                dependencies[aid] = deps

    return N, K, assignments, dependencies


def validate_schedule(schedule, assignments, dependencies, N, K, max_days):
    completed = set()
    daily_usage = {}

    for day, student, assignment in schedule:
        if day > max_days:
            return False

        # Each assignment exactly once
        if assignment in completed:
            return False

        # Dependencies
        if not all(dep in completed for dep in dependencies[assignment]):
            return False

        # Prompt usage per student per day
        daily_usage.setdefault(day, [0]*N)
        daily_usage[day][student] += assignments[assignment]

        if daily_usage[day][student] > K:
            return False

        completed.add(assignment)

    return len(completed) == len(assignments)


def all_dependencies_done(a, completed, dependencies):
    return all(dep in completed for dep in dependencies[a])


def bfs(N, K, assignments, dependencies, max_days):
    initial_state = (frozenset(), 1, tuple([0] * N), [])
    queue = deque([initial_state])
    results = []

    while queue:
        completed, day, prompt_used, schedule = queue.popleft()

        # All assignments completed
        if len(completed) == len(assignments):
            results.append(schedule)
            continue

        if day > max_days:
            continue

        expanded = False

        for a in assignments:
            if a in completed:
                continue
            if not all_dependencies_done(a, completed, dependencies):
                continue

            for s in range(N):
                if prompt_used[s] + assignments[a] <= K:
                    expanded = True

                    new_completed = set(completed)
                    new_completed.add(a)

                    new_prompt = list(prompt_used)
                    new_prompt[s] += assignments[a]

                    new_schedule = schedule + [(day, s, a)]

                    queue.append((
                        frozenset(new_completed),
                        day,
                        tuple(new_prompt),
                        new_schedule
                    ))

        # Move to next day if nothing could be scheduled today
        if not expanded:
            queue.append((
                completed,
                day + 1,
                tuple([0] * N),
                schedule
            ))

    return results


def main():
    if len(sys.argv) != 3:
        print("Usage: python scheduler.py <input-file> <number-of-days>")
        return

    filename = sys.argv[1]
    max_days = int(sys.argv[2])

    N, K, assignments, dependencies = parse_input(filename)

    results = bfs(N, K, assignments, dependencies, max_days)

    print(f"Total valid schedules: {len(results)}\n")
    for i, sch in enumerate(results, 1):
        print(f"Schedule {i}:")
        for day, student, assignment in sch:
            print(f"  Day {day}: Student {student + 1} → {assignment}")
        print()

    for sch in results:
        assert validate_schedule(sch, assignments, dependencies, N, K, max_days)



if __name__ == "__main__":
    main()
