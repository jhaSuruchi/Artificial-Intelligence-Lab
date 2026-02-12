import sys
from collections import deque

# ---------------------------------------------------------
# Input Parsing
# ---------------------------------------------------------

def parse_input(filename):
    assignments = {}
    dependencies = {}

    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue

            parts = line.split()
            if parts[0] == 'A':
                aid = f"A{parts[1]}"
                cost = int(parts[2])
                deps = []
                for d in parts[3:]:
                    if d == '0':
                        break
                    deps.append(f"A{d}")
                assignments[aid] = cost
                dependencies[aid] = deps

    return assignments, dependencies


# ---------------------------------------------------------
# Dependency Check (CRITICAL FIX)
# ---------------------------------------------------------

def can_do_today(a, student, shared_knowledge, solved_today, dependencies):
    for dep in dependencies[a]:
        if dep in shared_knowledge:
            continue
        if dep in solved_today[student]:
            continue
        return False
    return True


# ---------------------------------------------------------
# Part 3(b): Minimum K with delayed sharing
# ---------------------------------------------------------

def can_finish_delayed(assignments, dependencies, N, K, max_days):

    def dfs(completed, day, prompts, shared_knowledge, solved_today):
        if completed == set(assignments.keys()):
            return True

        if day > max_days:
            return False

        progress = False

        for a in assignments:
            if a in completed:
                continue

            for s in range(N):
                if not can_do_today(a, s, shared_knowledge, solved_today, dependencies):
                    continue
                if prompts[s] + assignments[a] <= K:
                    progress = True

                    completed.add(a)
                    prompts[s] += assignments[a]
                    solved_today[s].add(a)

                    if dfs(completed, day, prompts, shared_knowledge, solved_today):
                        return True

                    solved_today[s].remove(a)
                    prompts[s] -= assignments[a]
                    completed.remove(a)

        # Advance day → share knowledge
        if not progress:
            new_shared = set(completed)
            new_solved_today = [set() for _ in range(N)]
            return dfs(
                completed,
                day + 1,
                [0] * N,
                new_shared,
                new_solved_today
            )

        return False

    return dfs(
        set(),
        1,
        [0] * N,
        set(),
        [set() for _ in range(N)]
    )


def feasible_with_unlimited_prompts(assignments, dependencies, N, max_days):
    BIG_K = sum(assignments.values())
    return can_finish_delayed(assignments, dependencies, N, BIG_K, max_days)


def minimum_K_delayed(assignments, dependencies, N, max_days):
    if not feasible_with_unlimited_prompts(assignments, dependencies, N, max_days):
        return None

    K = 1
    while True:
        if can_finish_delayed(assignments, dependencies, N, K, max_days):
            return K
        K += 1


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------

def main():
    if len(sys.argv) != 5:
        print("Usage:")
        print("python assg02.py <input-file> part3b <N> <days>")
        return

    filename = sys.argv[1]
    mode = sys.argv[2]
    N = int(sys.argv[3])
    days = int(sys.argv[4])

    assignments, dependencies = parse_input(filename)

    if mode == "part3b":
        res = minimum_K_delayed(assignments, dependencies, N, days)
        if res is None:
            print("Result: IMPOSSIBLE within given days")
        else:
            print("Minimum prompts per student per day (delayed sharing):", res)
    else:
        print("Invalid mode")


if __name__ == "__main__":
    main()
