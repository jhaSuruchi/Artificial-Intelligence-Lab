import sys
import heapq
from math import ceil
from collections import defaultdict

# =========================================================
# Parsing
# =========================================================

def parse_input(filename):
    assignments = {}
    deps = defaultdict(list)

    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue

            parts = line.split()
            if parts[0] == 'A':
                aid = int(parts[1])
                cost = int(parts[2])
                dep_list = []
                for d in parts[3:]:
                    if d == '0':
                        break
                    dep_list.append(int(d))
                assignments[aid] = cost
                deps[aid] = dep_list

    return assignments, deps


# =========================================================
# Utility
# =========================================================

def is_gpt(a):
    return a % 2 == 0


def all_deps_done(a, completed, deps):
    return all(d in completed for d in deps[a])


# =========================================================
# Heuristic (Admissible)
# =========================================================

def heuristic(state_completed, assignments, deps, gpt_limit, gem_limit):
    remaining = [a for a in assignments if a not in state_completed]

    if not remaining:
        return 0

    rem_gpt = sum(assignments[a] for a in remaining if is_gpt(a))
    rem_gem = sum(assignments[a] for a in remaining if not is_gpt(a))

    prompt_bound = max(
        ceil(rem_gpt / gpt_limit) if gpt_limit else float('inf'),
        ceil(rem_gem / gem_limit) if gem_limit else float('inf')
    )

    # dependency depth lower bound
    memo = {}

    def depth(a):
        if a in memo:
            return memo[a]
        if not deps[a]:
            memo[a] = 1
        else:
            memo[a] = 1 + max(depth(d) for d in deps[a])
        return memo[a]

    dep_bound = max(depth(a) for a in remaining)

    return max(prompt_bound, dep_bound)


# =========================================================
# CASE A: One assignment per day (A*)
# =========================================================

def astar_caseA(assignments, deps, gpt_limit, gem_limit):
    nodes = 0
    counter = 0

    start_completed = frozenset()

    open_list = []
    heapq.heappush(open_list, (0, counter, start_completed, 1))

    visited = set()

    while open_list:
        f, _, completed, day = heapq.heappop(open_list)
        nodes += 1

        if completed == frozenset(assignments.keys()):
            return day - 1, nodes

        if completed in visited:
            continue
        visited.add(completed)

        for a in assignments:
            if a in completed:
                continue
            if not all_deps_done(a, completed, deps):
                continue

            new_completed = set(completed)
            new_completed.add(a)
            new_completed = frozenset(new_completed)

            g = day
            h = heuristic(new_completed, assignments, deps, gpt_limit, gem_limit)

            counter += 1
            heapq.heappush(open_list, (g + h, counter, new_completed, day + 1))

    return None, nodes


# =========================================================
# CASE B: Multiple per day + delayed sharing (DFBB)
# =========================================================

def dfbb_caseB(assignments, deps, gpt_limit, gem_limit, deadline=None):
    nodes = 0
    best = float('inf')

    def dfs(completed, day, gpt_left, gem_left, shared):
        nonlocal nodes, best
        nodes += 1

        if deadline and day > deadline:
            return

        if completed == set(assignments.keys()):
            best = min(best, day)
            return

        if day >= best:
            return

        progress = False

        for a in assignments:
            if a in completed:
                continue

            if not all_deps_done(a, shared, deps):
                continue

            if is_gpt(a):
                if gpt_left < assignments[a]:
                    continue
                next_gpt = gpt_left - assignments[a]
                next_gem = gem_left
            else:
                if gem_left < assignments[a]:
                    continue
                next_gem = gem_left - assignments[a]
                next_gpt = gpt_left

            progress = True
            completed.add(a)

            dfs(completed, day, next_gpt, next_gem, shared)

            completed.remove(a)

        if not progress:
            dfs(
                completed,
                day + 1,
                gpt_limit,
                gem_limit,
                set(completed)
            )

    dfs(set(), 1, gpt_limit, gem_limit, set())

    if best == float('inf'):
        return None, nodes
    return best - 1, nodes


# =========================================================
# QUERY 2: Min subscription cost
# =========================================================

def find_min_cost(assignments, deps, deadline, c1, c2, case_type):
    max_prompt = sum(assignments.values())

    best_cost = float('inf')
    best_scheme = None
    total_nodes = 0

    for gpt in range(1, max_prompt + 1):
        for gem in range(1, max_prompt + 1):

            cost = gpt * c1 + gem * c2
            if cost >= best_cost:
                continue

            if case_type == "A":
                days, nodes = astar_caseA(assignments, deps, gpt, gem)
            else:
                days, nodes = dfbb_caseB(assignments, deps, gpt, gem, deadline)

            total_nodes += nodes

            if days is not None and days <= deadline:
                best_cost = cost
                best_scheme = (gpt, gem)

    return best_scheme, best_cost if best_scheme else None, total_nodes


# =========================================================
# MAIN
# =========================================================

def main():
    if len(sys.argv) < 5:
        print("Usage:")
        print("Query-1: python assg03.py input.txt A 1 gpt gem")
        print("Query-2: python assg03.py input.txt B 2 deadline c1 c2")
        return

    filename = sys.argv[1]
    case_type = sys.argv[2]
    query = sys.argv[3]

    assignments, deps = parse_input(filename)

    if query == "1":
        gpt = int(sys.argv[4])
        gem = int(sys.argv[5])

        if case_type == "A":
            days, nodes = astar_caseA(assignments, deps, gpt, gem)
        else:
            days, nodes = dfbb_caseB(assignments, deps, gpt, gem)

        print("Earliest Completion:", days if days else "IMPOSSIBLE")
        print("Nodes Expanded:", nodes)

    elif query == "2":
        deadline = int(sys.argv[4])
        c1 = int(sys.argv[5])
        c2 = int(sys.argv[6])

        scheme, cost, nodes = find_min_cost(assignments, deps, deadline, c1, c2, case_type)

        if scheme:
            print("Best Scheme (GPT, Gemini):", scheme)
            print("Minimum Cost:", cost)
        else:
            print("IMPOSSIBLE within deadline")

        print("Nodes Expanded:", nodes)


if __name__ == "__main__":
    main()
