import sys
from copy import deepcopy

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



def dfs_with_slack(
    completed,
    day,
    prompt_used,
    schedule,
    N,
    K,
    assignments,
    dependencies,
    max_days,
    results
):
    # Goal condition
    if len(completed) == len(assignments):
        results.append(schedule.copy())
        return

    # Day limit exceeded
    if day > max_days:
        return

    # Try all assignment actions
    for a in assignments:
        if a in completed:
            continue

        # Dependency check
        if not all(dep in completed for dep in dependencies[a]):
            continue

        for s in range(N):
            if prompt_used[s] + assignments[a] <= K:
                # Apply action
                completed.add(a)
                prompt_used[s] += assignments[a]
                schedule.append((day, s, a))

                dfs_with_slack(
                    completed,
                    day,
                    prompt_used,
                    schedule,
                    N,
                    K,
                    assignments,
                    dependencies,
                    max_days,
                    results
                )

                # Backtrack
                schedule.pop()
                prompt_used[s] -= assignments[a]
                completed.remove(a)

    # 🔹 SLACK ACTION (intentional idle)
    # Move to next day even if work is possible
    dfs_with_slack(
        completed,
        day + 1,
        [0] * N,
        schedule,
        N,
        K,
        assignments,
        dependencies,
        max_days,
        results
    )




def main():
    if len(sys.argv) != 3:
        print("Usage: python scheduler.py <input-file> <number-of-days>")
        return

    filename = sys.argv[1]
    max_days = int(sys.argv[2])

    N, K, assignments, dependencies = parse_input(filename)

    results = []
    dfs_with_slack(set(), 1, [0]*N, [],
        N, K, assignments, dependencies, max_days, results)
    

    for i, sch in enumerate(results, 1):
        print(f"Schedule {i}:")
        for day, student, assignment in sch:
            print(f"  Day {day}: Student {student+1} -> {assignment}")
        print()

    print(f"Total valid schedules: {len(results)}\n")
        

if __name__ == "__main__":
    main()


