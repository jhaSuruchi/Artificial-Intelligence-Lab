import sys
from collections import deque
from copy import deepcopy

# =========================================================
# Input Parsing
# =========================================================

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


# =========================================================
# Utility
# =========================================================

def deps_satisfied_local(a, local_knowledge, dependencies):
    return all(dep in local_knowledge for dep in dependencies[a])


# =========================================================
# PART 1
# Given N, K → earliest completion day (instant sharing)
# =========================================================

def earliest_completion(assignments, dependencies, N, K):
    initial = (frozenset(), 1, tuple([0]*N))
    queue = deque([initial])
    visited = set()

    while queue:
        completed, day, prompts = queue.popleft()

        if completed == frozenset(assignments.keys()):
            return day

        if (completed, day, prompts) in visited:
            continue
        visited.add((completed, day, prompts))

        progress = False

        for a in assignments:
            if a in completed:
                continue
            if not all(dep in completed for dep in dependencies[a]):
                continue

            for s in range(N):
                if prompts[s] + assignments[a] <= K:
                    progress = True
                    new_completed = set(completed)
                    new_completed.add(a)

                    new_prompts = list(prompts)
                    new_prompts[s] += assignments[a]

                    queue.append((
                        frozenset(new_completed),
                        day,
                        tuple(new_prompts)
                    ))

        if not progress:
            queue.append((completed, day + 1, tuple([0]*N)))

    return None


# =========================================================
# PART 2
# Given N, m → minimum K (instant sharing)
# =========================================================

def can_finish(assignments, dependencies, N, K, max_days):

    def dfs(completed, day, prompts):
        if completed == set(assignments.keys()):
            return True
        if day > max_days:
            return False

        progress = False

        for a in assignments:
            if a in completed:
                continue
            if not all(dep in completed for dep in dependencies[a]):
                continue

            for s in range(N):
                if prompts[s] + assignments[a] <= K:
                    progress = True
                    completed.add(a)
                    prompts[s] += assignments[a]

                    if dfs(completed, day, prompts):
                        return True

                    prompts[s] -= assignments[a]
                    completed.remove(a)

        if not progress:
            return dfs(completed, day + 1, [0]*N)

        return False

    return dfs(set(), 1, [0]*N)


def minimum_K(assignments, dependencies, N, max_days):
    K = 1
    while True:
        if can_finish(assignments, dependencies, N, K, max_days):
            return K
        K += 1


# =========================================================
# PART 3(a)
# Given N, K → earliest completion day (delayed sharing)
# =========================================================

def earliest_completion_delayed(assignments, dependencies, N, K):
    init_knowledge = tuple(frozenset() for _ in range(N))
    initial = (frozenset(), 1, tuple([0]*N), init_knowledge)

    queue = deque([initial])
    visited = set()

    while queue:
        completed, day, prompts, knowledge = queue.popleft()

        if completed == frozenset(assignments.keys()):
            return day

        state_id = (completed, day, prompts, knowledge)
        if state_id in visited:
            continue
        visited.add(state_id)

        progress = False

        # Solve assignment (same-day chaining allowed)
        for a in assignments:
            if a in completed:
                continue

            for s in range(N):
                if not deps_satisfied_local(a, knowledge[s], dependencies):
                    continue
                if prompts[s] + assignments[a] <= K:
                    progress = True

                    new_completed = set(completed)
                    new_completed.add(a)

                    new_prompts = list(prompts)
                    new_prompts[s] += assignments[a]

                    new_knowledge = [set(k) for k in knowledge]
                    new_knowledge[s].add(a)

                    queue.append((
                        frozenset(new_completed),
                        day,
                        tuple(new_prompts),
                        tuple(frozenset(k) for k in new_knowledge)
                    ))

        # Advance day → 6am sharing
        if not progress:
            shared = set(completed)
            new_knowledge = tuple(frozenset(shared) for _ in range(N))
            queue.append((
                completed,
                day + 1,
                tuple([0]*N),
                new_knowledge
            ))

    return None


# =========================================================
# PART 3(b)
# Given N, m → minimum K (delayed sharing)
# =========================================================

def can_finish_delayed(assignments, dependencies, N, K, max_days):

    def dfs(completed, day, prompts, knowledge):
        if completed == set(assignments.keys()):
            return True
        if day > max_days:
            return False

        progress = False

        for a in assignments:
            if a in completed:
                continue

            for s in range(N):
                if not deps_satisfied_local(a, knowledge[s], dependencies):
                    continue
                if prompts[s] + assignments[a] <= K:
                    progress = True

                    completed.add(a)
                    prompts[s] += assignments[a]
                    knowledge[s].add(a)

                    if dfs(completed, day, prompts, knowledge):
                        return True

                    knowledge[s].remove(a)
                    prompts[s] -= assignments[a]
                    completed.remove(a)

        if not progress:
            shared = set(completed)
            new_knowledge = [shared.copy() for _ in range(N)]
            return dfs(completed, day + 1, [0]*N, new_knowledge)

        return False

    return dfs(set(), 1, [0]*N, [set() for _ in range(N)])


def minimum_K_delayed(assignments, dependencies, N, max_days):
    K = 1
    while True:
        if can_finish_delayed(assignments, dependencies, N, K, max_days):
            return K
        K += 1



def main():
    if len(sys.argv) < 4:
        print("Usage:")
        print("python assg02.py <input-file> <mode> <params>")
        print("Modes:")
        print("  part1 <N> <K>")
        print("  part2 <N> <days>")
        print("  part3a <N> <K>")
        print("  part3b <N> <days>")
        return

    filename = sys.argv[1]
    mode = sys.argv[2]

    assignments, dependencies = parse_input(filename)

    if mode == "part1":
        N, K = int(sys.argv[3]), int(sys.argv[4])
        print("Earliest completion day:", earliest_completion(assignments, dependencies, N, K))

    elif mode == "part2":
        N, days = int(sys.argv[3]), int(sys.argv[4])
        print("Minimum prompts per student per day:", minimum_K(assignments, dependencies, N, days))

    elif mode == "part3a":
        N, K = int(sys.argv[3]), int(sys.argv[4])
        print("Earliest completion day (delayed sharing):",
              earliest_completion_delayed(assignments, dependencies, N, K))

    elif mode == "part3b":
        N, days = int(sys.argv[3]), int(sys.argv[4])
        print("Minimum prompts per student per day (delayed sharing):",
              minimum_K_delayed(assignments, dependencies, N, days))

    else:
        print("Invalid mode")


if __name__ == "__main__":
    main()
