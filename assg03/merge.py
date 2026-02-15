import sys
import heapq
from math import ceil
from collections import defaultdict

# =========================================================
# Parsing
# =========================================================

def parse_input(filename):
    """Parse input file and return assignments and dependencies."""
    assignments = {}
    deps = defaultdict(list)

    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('%'):
                continue
            parts = line.split()
            
            # Ignore N and K lines as per assignment instructions
            if parts[0] in ['N', 'K']:
                continue
                
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
# Utilities
# =========================================================

def is_gpt(a):
    """Check if assignment uses ChatGPT (even indexed)."""
    return a % 2 == 0


def deps_done(a, completed, deps):
    """Check if all dependencies for assignment a are completed."""
    return all(d in completed for d in deps[a])


# =========================================================
# Heuristic (Admissible)
# =========================================================

def heuristic(completed, assignments, deps, gpt_limit, gem_limit, case_type):
    """
    Admissible heuristic for both Case A and Case B.
    Returns minimum number of days needed to complete remaining assignments.
    """
    remaining = [a for a in assignments if a not in completed]
    if not remaining:
        return 0

    # For Case A: one assignment per day minimum
    if case_type == "A":
        return len(remaining)
    
    # For Case B: consider both prompt limits and dependencies
    rem_gpt = sum(assignments[a] for a in remaining if is_gpt(a))
    rem_gem = sum(assignments[a] for a in remaining if not is_gpt(a))

    # Prompt-based bound: minimum days needed based on daily limits
    prompt_bound = 0
    if gpt_limit > 0 and rem_gpt > 0:
        prompt_bound = max(prompt_bound, ceil(rem_gpt / gpt_limit))
    elif gpt_limit == 0 and rem_gpt > 0:
        return float('inf')
    
    if gem_limit > 0 and rem_gem > 0:
        prompt_bound = max(prompt_bound, ceil(rem_gem / gem_limit))
    elif gem_limit == 0 and rem_gem > 0:
        return float('inf')

    # Dependency-based bound: longest dependency chain
    memo = {}
    def depth(a):
        if a in memo:
            return memo[a]
        if a in completed:
            memo[a] = 0
        elif not deps[a] or all(d in completed for d in deps[a]):
            memo[a] = 1
        else:
            memo[a] = 1 + max(depth(d) for d in deps[a] if d not in completed)
        return memo[a]

    dep_bound = max(depth(a) for a in remaining) if remaining else 0
    
    return max(prompt_bound, dep_bound)


# =========================================================
# CASE A: One assignment per day
# =========================================================

def solve_caseA(algo, assignments, deps, gpt_limit, gem_limit, deadline=None):
    """
    Solve Case A: Each student can do only one assignment per day.
    Returns: (days, sequence, nodes_expanded)
    """
    nodes = 0
    best = float('inf')
    best_path = None

    if algo == "DFS":
        def dfs(completed, day, path):
            nonlocal nodes, best, best_path
            nodes += 1

            if deadline and day > deadline:
                return

            if completed == set(assignments.keys()):
                if day < best:
                    best = day
                    best_path = path.copy()
                return

            # Try assigning each available assignment
            for a in assignments:
                if a not in completed and deps_done(a, completed, deps):
                    # Check if we have enough prompts for this assignment
                    if is_gpt(a):
                        if assignments[a] > gpt_limit:
                            continue
                    else:
                        if assignments[a] > gem_limit:
                            continue
                    
                    completed.add(a)
                    dfs(completed, day + 1, path + [(day, a)])
                    completed.remove(a)

        dfs(set(), 1, [])

    elif algo == "DFBB":
        def dfbb(completed, day, path):
            nonlocal nodes, best, best_path
            nodes += 1

            if deadline and day > deadline:
                return

            if completed == set(assignments.keys()):
                if day < best:
                    best = day
                    best_path = path.copy()
                return

            # Prune if current path can't improve best
            if day >= best:
                return

            # Try assigning each available assignment
            for a in assignments:
                if a not in completed and deps_done(a, completed, deps):
                    # Check if we have enough prompts
                    if is_gpt(a):
                        if assignments[a] > gpt_limit:
                            continue
                    else:
                        if assignments[a] > gem_limit:
                            continue
                    
                    completed.add(a)
                    dfbb(completed, day + 1, path + [(day, a)])
                    completed.remove(a)

        dfbb(set(), 1, [])

    else:  # A*
        counter = 0
        open_list = []
        start_h = heuristic(frozenset(), assignments, deps, gpt_limit, gem_limit, "A")
        heapq.heappush(open_list, (start_h, counter, frozenset(), 1, []))
        visited = {}

        while open_list:
            f, _, completed, day, path = heapq.heappop(open_list)
            nodes += 1

            if completed == frozenset(assignments.keys()):
                return day - 1, path, nodes

            if deadline and day > deadline:
                continue

            # State: (completed assignments, day)
            state = (completed, day)
            if state in visited and visited[state] <= day:
                continue
            visited[state] = day

            # Try each available assignment
            for a in assignments:
                if a not in completed and deps_done(a, completed, deps):
                    # Check prompts
                    if is_gpt(a):
                        if assignments[a] > gpt_limit:
                            continue
                    else:
                        if assignments[a] > gem_limit:
                            continue
                    
                    new_completed = frozenset(set(completed) | {a})
                    new_path = path + [(day, a)]
                    new_day = day + 1

                    g = new_day
                    h = heuristic(new_completed, assignments, deps, 
                                gpt_limit, gem_limit, "A")

                    counter += 1
                    heapq.heappush(open_list, (g + h, counter, 
                                              new_completed, new_day, new_path))

    if best == float('inf'):
        return None, None, nodes
    return best - 1, best_path, nodes


# =========================================================
# CASE B: Multiple assignments per day with prompt limits
# =========================================================

def solve_caseB(algo, assignments, deps, gpt_limit, gem_limit, deadline=None):
    """
    Solve Case B: Multiple assignments per day, but limited by daily prompts.
    Students can share solutions only on the next day.
    Returns: (days, sequence, nodes_expanded)
    """
    nodes = 0
    best = float('inf')
    best_path = None

    if algo == "DFS":
        def dfs(completed, day, gpt_left, gem_left, shared, path):
            nonlocal nodes, best, best_path
            nodes += 1

            if deadline and day > deadline:
                return

            if completed == set(assignments.keys()):
                if day < best:
                    best = day
                    best_path = path.copy()
                return

            progress = False

            # Try doing each available assignment today
            for a in assignments:
                if a in completed:
                    continue
                if not deps_done(a, shared, deps):
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
                dfs(completed, day, next_gpt, next_gem, shared, path + [(day, a)])
                completed.remove(a)

            # Move to next day if no more progress today
            if not progress:
                dfs(completed, day + 1, gpt_limit, gem_limit, 
                   set(completed), path)

        dfs(set(), 1, gpt_limit, gem_limit, set(), [])

    elif algo == "DFBB":
        def dfbb(completed, day, gpt_left, gem_left, shared, path):
            nonlocal nodes, best, best_path
            nodes += 1

            if deadline and day > deadline:
                return

            if completed == set(assignments.keys()):
                if day < best:
                    best = day
                    best_path = path.copy()
                return

            # Prune if can't improve
            if day >= best:
                return

            progress = False

            for a in assignments:
                if a in completed:
                    continue
                if not deps_done(a, shared, deps):
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
                dfbb(completed, day, next_gpt, next_gem, shared, path + [(day, a)])
                completed.remove(a)

            if not progress:
                dfbb(completed, day + 1, gpt_limit, gem_limit,
                    set(completed), path)

        dfbb(set(), 1, gpt_limit, gem_limit, set(), [])

    else:  # A*
        counter = 0
        open_list = []
        start_h = heuristic(frozenset(), assignments, deps, 
                          gpt_limit, gem_limit, "B")
        start_state = (frozenset(), 1, gpt_limit, gem_limit, frozenset(), [])
        heapq.heappush(open_list, (1 + start_h, counter, start_state))
        visited = {}

        while open_list:
            f, _, state = heapq.heappop(open_list)
            completed, day, gpt_left, gem_left, shared, path = state
            nodes += 1

            if completed == frozenset(assignments.keys()):
                return day, path, nodes

            if deadline and day > deadline:
                continue

            # State: (completed, day, gpt_left, gem_left, shared)
            state_id = (completed, day, gpt_left, gem_left, shared)
            if state_id in visited:
                continue
            visited[state_id] = True

            progress = False

            for a in assignments:
                if a in completed:
                    continue
                if not deps_done(a, shared, deps):
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
                new_completed = frozenset(set(completed) | {a})
                new_path = path + [(day, a)]

                h = heuristic(new_completed, assignments, deps,
                            gpt_limit, gem_limit, "B")

                counter += 1
                new_state = (new_completed, day, next_gpt, next_gem, shared, new_path)
                heapq.heappush(open_list, (day + h, counter, new_state))

            if not progress:
                counter += 1
                new_state = (completed, day + 1, gpt_limit, gem_limit,
                           frozenset(completed), path)
                h = heuristic(completed, assignments, deps, 
                            gpt_limit, gem_limit, "B")
                heapq.heappush(open_list, (day + 1 + h, counter, new_state))

    if best == float('inf'):
        return None, None, nodes
    return best, best_path, nodes


# =========================================================
# QUERY 1 — Find earliest completion with given subscription
# =========================================================

def query1(case_type, assignments, deps, gpt_limit, gem_limit):
    """
    Query 1: Given subscription, find earliest way to finish all assignments.
    Compare DFS, DFBB, and A* algorithms.
    """
    print(f"\n{'='*60}")
    print(f"QUERY 1: Case {case_type}")
    print(f"Subscription: ChatGPT={gpt_limit}, Gemini={gem_limit} prompts/day")
    print(f"{'='*60}\n")

    for algo in ["DFS", "DFBB", "ASTAR"]:
        print(f"Algorithm: {algo}")
        print("-" * 40)

        if case_type == "A":
            days, seq, nodes = solve_caseA(algo, assignments, deps, 
                                          gpt_limit, gem_limit)
        else:
            days, seq, nodes = solve_caseB(algo, assignments, deps, 
                                          gpt_limit, gem_limit)

        if days is None:
            print("Result: NO SOLUTION")
        else:
            print(f"Minimum Days: {days}")
            print(f"Nodes Expanded: {nodes}")
            if seq:
                print("Schedule:")
                for d, a in seq:
                    llm = "ChatGPT" if is_gpt(a) else "Gemini"
                    print(f"  Day {d}: Assignment A{a} ({llm}, {assignments[a]} prompts)")
        print()


# =========================================================
# QUERY 2 — Find optimal subscription within deadline
# =========================================================

def query2(case_type, assignments, deps, deadline, c1, c2):
    """
    Query 2: Given deadline, find best subscription (minimum daily cost).
    c1 = cost per ChatGPT prompt
    c2 = cost per Gemini prompt
    """
    print(f"\n{'='*60}")
    print(f"QUERY 2: Case {case_type}")
    print(f"Deadline: {deadline} days")
    print(f"Costs: ChatGPT={c1}, Gemini={c2} per prompt")
    print(f"{'='*60}\n")

    # Calculate total prompts needed
    total_gpt = sum(assignments[a] for a in assignments if is_gpt(a))
    total_gem = sum(assignments[a] for a in assignments if not is_gpt(a))
    
    print(f"Total prompts needed: ChatGPT={total_gpt}, Gemini={total_gem}")
    print("\nSearching for optimal subscription...")
    print("-" * 40)

    best_cost = float('inf')
    best_scheme = None
    best_seq = None
    
    # For Case A, minimum subscription is max single assignment
    min_gpt = max((assignments[a] for a in assignments if is_gpt(a)), default=1)
    min_gem = max((assignments[a] for a in assignments if not is_gpt(a)), default=1)
    
    # For Case B, we might need more per day
    max_gpt = max(ceil(total_gpt / 1), total_gpt)  # Can't do faster than 1 day
    max_gem = max(ceil(total_gem / 1), total_gem)

    # Try different subscription combinations
    for gpt in range(min_gpt, min(max_gpt + 1, total_gpt + 1)):
        for gem in range(min_gem, min(max_gem + 1, total_gem + 1)):
            cost = gpt * c1 + gem * c2
            
            # Skip if already more expensive than best found
            if cost >= best_cost:
                continue

            # Try this subscription with A*
            if case_type == "A":
                days, seq, _ = solve_caseA("ASTAR", assignments, deps, 
                                          gpt, gem, deadline)
            else:
                days, seq, _ = solve_caseB("ASTAR", assignments, deps, 
                                          gpt, gem, deadline)

            if days is not None and days <= deadline:
                print(f"  Found solution: ChatGPT={gpt}, Gemini={gem}, "
                      f"Cost={cost}, Days={days}")
                if cost < best_cost:
                    best_cost = cost
                    best_scheme = (gpt, gem)
                    best_seq = seq

    print("\n" + "=" * 60)
    if best_scheme is None:
        print("Result: IMPOSSIBLE - No subscription scheme meets deadline")
    else:
        print(f"Optimal Subscription: ChatGPT={best_scheme[0]}, "
              f"Gemini={best_scheme[1]} prompts/day")
        print(f"Minimum Daily Cost: {best_cost}")
        print(f"\nOptimal Schedule:")
        for d, a in best_seq:
            llm = "ChatGPT" if is_gpt(a) else "Gemini"
            print(f"  Day {d}: Assignment A{a} ({llm}, {assignments[a]} prompts)")
    print("=" * 60)


# =========================================================
# MAIN
# =========================================================

def main():
    if len(sys.argv) < 3:
        print("Usage for Query 1: python assignment3.py <input-file> <case> 1 <gpt-limit> <gem-limit>")
        print("Usage for Query 2: python assignment3.py <input-file> <case> 2 <deadline> <c1> <c2>")
        sys.exit(1)

    filename = sys.argv[1]
    case_type = sys.argv[2].upper()
    query = sys.argv[3]

    if case_type not in ["A", "B"]:
        print("Error: Case must be 'A' or 'B'")
        sys.exit(1)

    assignments, deps = parse_input(filename)
    
    print(f"\nLoaded {len(assignments)} assignments from {filename}")
    print(f"Assignments: {sorted(assignments.keys())}")

    if query == "1":
        if len(sys.argv) != 6:
            print("Error: Query 1 requires: <gpt-limit> <gem-limit>")
            sys.exit(1)
        
        gpt_limit = int(sys.argv[4])
        gem_limit = int(sys.argv[5])
        query1(case_type, assignments, deps, gpt_limit, gem_limit)

    elif query == "2":
        if len(sys.argv) != 7:
            print("Error: Query 2 requires: <deadline> <c1> <c2>")
            sys.exit(1)
        
        deadline = int(sys.argv[4])
        c1 = int(sys.argv[5])
        c2 = int(sys.argv[6])
        query2(case_type, assignments, deps, deadline, c1, c2)

    else:
        print("Error: Query must be '1' or '2'")
        sys.exit(1)


if __name__ == "__main__":
    main()