"""
seed.py - Seed 50 popular LeetCode problems with accurate per-tier complexity targets.
Run: python -m app.db.seed   (from backend/)
"""
from __future__ import annotations
import asyncio

PROBLEMS = [
    {
        "slug": "two-sum",
        "title": "Two Sum",
        "difficulty": "Easy",
        "category": "Array",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(1)", "approach_name": "Nested Loop", "description": "Check every pair (i,j) for nums[i]+nums[j]==target"},
            {"tier": "BETTER", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Sort + Two Pointers", "description": "Sort array, use two pointers from both ends"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Hash Map", "description": "Single pass: store complement â†’ index in a hash map"},
        ],
    },
    {
        "slug": "add-two-numbers",
        "title": "Add Two Numbers",
        "difficulty": "Medium",
        "category": "Linked List",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Convert to Int", "description": "Traverse lists, convert to integers, add, convert back"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Iterative with Carry", "description": "Traverse both lists simultaneously tracking carry"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "In-place Carry", "description": "Reuse existing nodes, only allocate new nodes when needed"},
        ],
    },
    {
        "slug": "longest-substring-without-repeating-characters",
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "Medium",
        "category": "Sliding Window",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ³)", "space_complexity": "O(min(N,M))", "approach_name": "Check All Substrings", "description": "Generate all substrings, check each for duplicates"},
            {"tier": "BETTER", "time_complexity": "O(NÂ²)", "space_complexity": "O(min(N,M))", "approach_name": "Two Pointer Naive", "description": "Expand window, restart from i+1 on duplicate"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(min(N,M))", "approach_name": "Sliding Window + HashMap", "description": "Jump left pointer to last seen position of duplicate"},
        ],
    },
    {
        "slug": "median-of-two-sorted-arrays",
        "title": "Median of Two Sorted Arrays",
        "difficulty": "Hard",
        "category": "Binary Search",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O((N+M) log(N+M))", "space_complexity": "O(N+M)", "approach_name": "Merge and Sort", "description": "Merge arrays, sort, find middle element"},
            {"tier": "BETTER", "time_complexity": "O(N+M)", "space_complexity": "O(1)", "approach_name": "Two Pointer Merge", "description": "Merge virtually using two pointers, stop at median"},
            {"tier": "OPTIMAL", "time_complexity": "O(log(min(N,M)))", "space_complexity": "O(1)", "approach_name": "Binary Search on Partition", "description": "Binary search partition on the smaller array"},
        ],
    },
    {
        "slug": "longest-palindromic-substring",
        "title": "Longest Palindromic Substring",
        "difficulty": "Medium",
        "category": "Dynamic Programming",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ³)", "space_complexity": "O(1)", "approach_name": "Check All Substrings", "description": "Generate all O(NÂ²) substrings, verify each in O(N)"},
            {"tier": "BETTER", "time_complexity": "O(NÂ²)", "space_complexity": "O(NÂ²)", "approach_name": "DP Table", "description": "dp[i][j]=True if s[i..j] is palindrome, fill diagonally"},
            {"tier": "OPTIMAL", "time_complexity": "O(NÂ²)", "space_complexity": "O(1)", "approach_name": "Expand Around Center", "description": "For each center (2N-1 centers), expand while palindrome"},
        ],
    },
    {
        "slug": "container-with-most-water",
        "title": "Container With Most Water",
        "difficulty": "Medium",
        "category": "Two Pointers",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(1)", "approach_name": "Check All Pairs", "description": "For each pair (i,j) compute min(h[i],h[j])*(j-i)"},
            {"tier": "BETTER", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Sort by Height", "description": "Sort indices by height, track max width seen"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Two Pointers", "description": "Move the shorter pointer inward â€” greedy proof by contradiction"},
        ],
    },
    {
        "slug": "3sum",
        "title": "3Sum",
        "difficulty": "Medium",
        "category": "Two Pointers",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ³)", "space_complexity": "O(1)", "approach_name": "Triple Loop", "description": "Check every triplet (i,j,k) for nums[i]+nums[j]+nums[k]==0"},
            {"tier": "BETTER", "time_complexity": "O(NÂ²)", "space_complexity": "O(N)", "approach_name": "Fix + Hash Set", "description": "Fix i, use hash set for two-sum on remaining elements"},
            {"tier": "OPTIMAL", "time_complexity": "O(NÂ²)", "space_complexity": "O(1)", "approach_name": "Sort + Two Pointers", "description": "Sort, fix i, use two pointers for remaining; skip duplicates"},
        ],
    },
    {
        "slug": "valid-parentheses",
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "category": "Stack",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(N)", "approach_name": "Repeated Removal", "description": "Repeatedly remove matching pairs until none remain"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Counter", "description": "Count opens/closes (only works for single bracket type)"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Stack", "description": "Push open brackets; on close, check stack top matches"},
        ],
    },
    {
        "slug": "merge-two-sorted-lists",
        "title": "Merge Two Sorted Lists",
        "difficulty": "Easy",
        "category": "Linked List",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N+M)", "space_complexity": "O(N+M)", "approach_name": "Collect and Sort", "description": "Collect all values, sort, build new list"},
            {"tier": "BETTER", "time_complexity": "O(N+M)", "space_complexity": "O(N+M)", "approach_name": "Recursive", "description": "Recurse: pick smaller head, recurse on remaining"},
            {"tier": "OPTIMAL", "time_complexity": "O(N+M)", "space_complexity": "O(1)", "approach_name": "Iterative with Dummy", "description": "Use dummy head, always advance the smaller pointer"},
        ],
    },
    {
        "slug": "best-time-to-buy-and-sell-stock",
        "title": "Best Time to Buy and Sell Stock",
        "difficulty": "Easy",
        "category": "Array",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(1)", "approach_name": "Try All Pairs", "description": "For every (i,j) pair with i<j, compute profit"},
            {"tier": "BETTER", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Sort Indices", "description": "Track min price index and try all sell days"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Single Pass Min Tracking", "description": "Track running min price; max profit = max(price - min_so_far)"},
        ],
    },
    {
        "slug": "valid-palindrome",
        "title": "Valid Palindrome",
        "difficulty": "Easy",
        "category": "Two Pointers",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Filter and Reverse", "description": "Filter alphanumeric, compare with reverse"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Filter + Two Pointer", "description": "Filter to new string, then two pointers from both ends"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "In-place Two Pointers", "description": "Skip non-alphanumeric in-place; no extra string allocation"},
        ],
    },
    {
        "slug": "climbing-stairs",
        "title": "Climbing Stairs",
        "difficulty": "Easy",
        "category": "Dynamic Programming",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(2^N)", "space_complexity": "O(N)", "approach_name": "Recursion", "description": "Recursive DFS: ways(n) = ways(n-1) + ways(n-2)"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Memoization / DP Array", "description": "Top-down with memo or bottom-up DP table"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Fibonacci (2 Variables)", "description": "Only keep prev two values; recognize as Fibonacci sequence"},
        ],
    },
    {
        "slug": "binary-search",
        "title": "Binary Search",
        "difficulty": "Easy",
        "category": "Binary Search",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Linear Scan", "description": "Scan array left to right until target found"},
            {"tier": "BETTER", "time_complexity": "O(log N)", "space_complexity": "O(log N)", "approach_name": "Recursive Binary Search", "description": "Recursively halve search space (uses call stack)"},
            {"tier": "OPTIMAL", "time_complexity": "O(log N)", "space_complexity": "O(1)", "approach_name": "Iterative Binary Search", "description": "While lo<=hi: mid=(lo+hi)//2, adjust lo/hi based on comparison"},
        ],
    },
    {
        "slug": "reverse-linked-list",
        "title": "Reverse Linked List",
        "difficulty": "Easy",
        "category": "Linked List",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Collect and Rebuild", "description": "Store all values in array, rebuild list in reverse"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Recursive", "description": "Recurse to end; on the way back, reverse next pointer"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Iterative 3-Pointer", "description": "prev=None, curr=head; while curr: next=curr.next; curr.next=prev; prev=curr; curr=next"},
        ],
    },
    {
        "slug": "linked-list-cycle",
        "title": "Linked List Cycle",
        "difficulty": "Easy",
        "category": "Linked List",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Hash Set", "description": "Store visited nodes in a set; cycle if revisited"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Timestamp Marking", "description": "Mark each node with a visit timestamp"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Floyd's Cycle Detection", "description": "Slow/fast pointers; cycle exists if they meet"},
        ],
    },
    {
        "slug": "maximum-depth-of-binary-tree",
        "title": "Maximum Depth of Binary Tree",
        "difficulty": "Easy",
        "category": "Tree",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "BFS Level Count", "description": "BFS, count the number of levels"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(H)", "approach_name": "DFS Recursive", "description": "return 1 + max(dfs(left), dfs(right)); O(H) stack space"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(H)", "approach_name": "Iterative DFS (Stack)", "description": "Use explicit stack with (node, depth) pairs; no recursion overhead"},
        ],
    },
    {
        "slug": "invert-binary-tree",
        "title": "Invert Binary Tree",
        "difficulty": "Easy",
        "category": "Tree",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Serialize and Rebuild", "description": "Serialize tree, rebuild with children swapped"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Recursive", "description": "node.left, node.right = invert(node.right), invert(node.left)"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(W)", "approach_name": "BFS Queue", "description": "BFS with a queue; swap children as you dequeue each node; O(W) where W = max width"},
        ],
    },
    {
        "slug": "number-of-1-bits",
        "title": "Number of 1 Bits",
        "difficulty": "Easy",
        "category": "Bit Manipulation",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(log N)", "space_complexity": "O(1)", "approach_name": "String Conversion", "description": "Convert to binary string, count '1' characters"},
            {"tier": "BETTER", "time_complexity": "O(log N)", "space_complexity": "O(1)", "approach_name": "Bit Shifting", "description": "Right-shift n each step, count when LSB is 1"},
            {"tier": "OPTIMAL", "time_complexity": "O(K)", "space_complexity": "O(1)", "approach_name": "Brian Kernighan n &= (n-1)", "description": "n &= n-1 clears lowest set bit; repeat until n=0; K = number of set bits"},
        ],
    },
    {
        "slug": "house-robber",
        "title": "House Robber",
        "difficulty": "Medium",
        "category": "Dynamic Programming",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(2^N)", "space_complexity": "O(N)", "approach_name": "Recursion", "description": "At each house: rob(skip next) or skip; exponential branches"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "DP Array", "description": "dp[i] = max(dp[i-1], dp[i-2] + nums[i])"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Two Variables", "description": "Only track prev2 and prev1; rolling update"},
        ],
    },
    {
        "slug": "coin-change",
        "title": "Coin Change",
        "difficulty": "Medium",
        "category": "Dynamic Programming",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(S^N)", "space_complexity": "O(N)", "approach_name": "Recursive DFS", "description": "Try every combination recursively"},
            {"tier": "BETTER", "time_complexity": "O(S*N)", "space_complexity": "O(S)", "approach_name": "Top-Down Memoization", "description": "Memoize results for each remaining amount"},
            {"tier": "OPTIMAL", "time_complexity": "O(S*N)", "space_complexity": "O(S)", "approach_name": "Bottom-Up DP", "description": "dp[i] = min coins for amount i; fill from 0 to amount"},
        ],
    },
    {
        "slug": "number-of-islands",
        "title": "Number of Islands",
        "difficulty": "Medium",
        "category": "Graph",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O((N*M)Â²)", "space_complexity": "O(N*M)", "approach_name": "Check Each Cell Independently", "description": "For each unvisited land cell, run full BFS repeatedly"},
            {"tier": "BETTER", "time_complexity": "O(N*M)", "space_complexity": "O(N*M)", "approach_name": "BFS/DFS", "description": "For each unvisited '1', flood-fill with BFS/DFS, increment count"},
            {"tier": "OPTIMAL", "time_complexity": "O(N*M * Î±(N*M))", "space_complexity": "O(N*M)", "approach_name": "Union-Find", "description": "Union adjacent land cells; count distinct roots"},
        ],
    },
    {
        "slug": "meeting-rooms",
        "title": "Meeting Rooms",
        "difficulty": "Easy",
        "category": "Intervals",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(1)", "approach_name": "Check All Pairs", "description": "For every pair of meetings, check if they overlap"},
            {"tier": "BETTER", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Sort by End Time", "description": "Sort by end, check if any start < prev end"},
            {"tier": "OPTIMAL", "time_complexity": "O(N log N)", "space_complexity": "O(1)", "approach_name": "Sort by Start", "description": "Sort by start time; one pass to check overlap with previous"},
        ],
    },
    {
        "slug": "product-of-array-except-self",
        "title": "Product of Array Except Self",
        "difficulty": "Medium",
        "category": "Array",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(N)", "approach_name": "Nested Loop", "description": "For each element, multiply all other elements"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Prefix + Suffix Arrays", "description": "Build prefix products array and suffix products array, multiply"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Running Product", "description": "Fill output with prefix products in one pass; multiply suffix in reverse pass"},
        ],
    },
    {
        "slug": "find-minimum-in-rotated-sorted-array",
        "title": "Find Minimum in Rotated Sorted Array",
        "difficulty": "Medium",
        "category": "Binary Search",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Linear Scan", "description": "Scan for the element smaller than its predecessor"},
            {"tier": "BETTER", "time_complexity": "O(log N)", "space_complexity": "O(log N)", "approach_name": "Recursive Binary Search", "description": "Binary search; recurse on the unsorted half"},
            {"tier": "OPTIMAL", "time_complexity": "O(log N)", "space_complexity": "O(1)", "approach_name": "Iterative Binary Search", "description": "If mid > right: min is in right half; else in left half; converge"},
        ],
    },
    {
        "slug": "search-in-rotated-sorted-array",
        "title": "Search in Rotated Sorted Array",
        "difficulty": "Medium",
        "category": "Binary Search",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Linear Search", "description": "Scan the full array for target"},
            {"tier": "BETTER", "time_complexity": "O(log N + K)", "space_complexity": "O(1)", "approach_name": "Find Pivot then Binary Search", "description": "Find rotation point first, then binary search in correct half"},
            {"tier": "OPTIMAL", "time_complexity": "O(log N)", "space_complexity": "O(1)", "approach_name": "Modified Binary Search", "description": "In each step, determine which half is sorted; adjust bounds accordingly"},
        ],
    },
    {
        "slug": "combination-sum",
        "title": "Combination Sum",
        "difficulty": "Medium",
        "category": "Backtracking",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N^(T/M))", "space_complexity": "O(T/M)", "approach_name": "Pure Recursion", "description": "Try all combinations with repetition, no pruning"},
            {"tier": "BETTER", "time_complexity": "O(N^(T/M))", "space_complexity": "O(T/M)", "approach_name": "Backtracking with Sort", "description": "Sort candidates; prune branch when remainder < 0"},
            {"tier": "OPTIMAL", "time_complexity": "O(N^(T/M))", "space_complexity": "O(T/M)", "approach_name": "Backtracking from Index", "description": "Start each recursion from current index to avoid duplicates; no need to sort"},
        ],
    },
    {
        "slug": "word-search",
        "title": "Word Search",
        "difficulty": "Medium",
        "category": "Backtracking",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N*M * 4^L)", "space_complexity": "O(L)", "approach_name": "DFS Without Visited Marking", "description": "DFS from every cell, may revisit cells"},
            {"tier": "BETTER", "time_complexity": "O(N*M * 4^L)", "space_complexity": "O(N*M)", "approach_name": "DFS + Visited Set", "description": "DFS with a visited set to avoid revisiting cells"},
            {"tier": "OPTIMAL", "time_complexity": "O(N*M * 4^L)", "space_complexity": "O(L)", "approach_name": "DFS + In-place Marking", "description": "Temporarily mark cell as '#' to avoid revisit; restore after backtrack"},
        ],
    },
    {
        "slug": "jump-game",
        "title": "Jump Game",
        "difficulty": "Medium",
        "category": "Greedy",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N^N)", "space_complexity": "O(N)", "approach_name": "Recursive DFS", "description": "Try all possible jumps from each position recursively"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "DP from Right", "description": "dp[i]=True if can reach end from i; fill right to left"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Greedy Max Reach", "description": "Track max reachable index; if i > max_reach, return False"},
        ],
    },
    {
        "slug": "unique-paths",
        "title": "Unique Paths",
        "difficulty": "Medium",
        "category": "Dynamic Programming",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(2^(M+N))", "space_complexity": "O(M+N)", "approach_name": "Recursion", "description": "At each cell: paths(m,n)=paths(m-1,n)+paths(m,n-1)"},
            {"tier": "BETTER", "time_complexity": "O(M*N)", "space_complexity": "O(M*N)", "approach_name": "2D DP Table", "description": "Fill grid: dp[i][j] = dp[i-1][j] + dp[i][j-1]"},
            {"tier": "OPTIMAL", "time_complexity": "O(M*N)", "space_complexity": "O(N)", "approach_name": "1D DP Rolling Array", "description": "Only keep one row; update in-place left to right"},
        ],
    },
    {
        "slug": "word-break",
        "title": "Word Break",
        "difficulty": "Medium",
        "category": "Dynamic Programming",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(2^N)", "space_complexity": "O(N)", "approach_name": "Recursion", "description": "Try all possible splits recursively"},
            {"tier": "BETTER", "time_complexity": "O(NÂ² * M)", "space_complexity": "O(N)", "approach_name": "Memoized Recursion", "description": "Cache results for each start index"},
            {"tier": "OPTIMAL", "time_complexity": "O(NÂ² * M)", "space_complexity": "O(N)", "approach_name": "Bottom-Up DP", "description": "dp[i]=True if s[:i] breakable; try all j<i where dp[j] and s[j:i] in dict"},
        ],
    },
    {
        "slug": "longest-increasing-subsequence",
        "title": "Longest Increasing Subsequence",
        "difficulty": "Medium",
        "category": "Dynamic Programming",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(2^N)", "space_complexity": "O(N)", "approach_name": "Recursion", "description": "Try including/excluding each element"},
            {"tier": "BETTER", "time_complexity": "O(NÂ²)", "space_complexity": "O(N)", "approach_name": "DP Array", "description": "dp[i] = LIS ending at index i; dp[i] = max(dp[j]+1) for j<i, nums[j]<nums[i]"},
            {"tier": "OPTIMAL", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Binary Search + Patience Sort", "description": "Maintain tails[] array; binary search insertion point for each element"},
        ],
    },
    {
        "slug": "course-schedule",
        "title": "Course Schedule",
        "difficulty": "Medium",
        "category": "Graph",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(V * (V+E))", "space_complexity": "O(V+E)", "approach_name": "DFS from Each Node", "description": "Run DFS from each unvisited node to detect cycle"},
            {"tier": "BETTER", "time_complexity": "O(V+E)", "space_complexity": "O(V+E)", "approach_name": "DFS with 3-Color", "description": "0=unvisited, 1=visiting, 2=done; cycle if we hit a 1"},
            {"tier": "OPTIMAL", "time_complexity": "O(V+E)", "space_complexity": "O(V+E)", "approach_name": "Kahn's BFS (Topological Sort)", "description": "Process nodes with in-degree 0; if all processed â†’ no cycle"},
        ],
    },
    {
        "slug": "clone-graph",
        "title": "Clone Graph",
        "difficulty": "Medium",
        "category": "Graph",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N+E)", "space_complexity": "O(N+E)", "approach_name": "BFS + Two-Pass", "description": "First collect all nodes, then clone, then rewire edges"},
            {"tier": "BETTER", "time_complexity": "O(N+E)", "space_complexity": "O(N+E)", "approach_name": "DFS Recursive", "description": "DFS: clone node, recurse for each neighbor; use hash map for visited"},
            {"tier": "OPTIMAL", "time_complexity": "O(N+E)", "space_complexity": "O(N+E)", "approach_name": "BFS Iterative", "description": "BFS with queue; clone each node once, map oldâ†’new, add neighbors"},
        ],
    },
    {
        "slug": "pacific-atlantic-water-flow",
        "title": "Pacific Atlantic Water Flow",
        "difficulty": "Medium",
        "category": "Graph",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O((N*M)Â²)", "space_complexity": "O(N*M)", "approach_name": "DFS from Every Cell", "description": "From each cell, DFS to check if both oceans reachable"},
            {"tier": "BETTER", "time_complexity": "O(N*M)", "space_complexity": "O(N*M)", "approach_name": "DFS from Borders", "description": "Two DFS: one from Pacific border, one from Atlantic; find intersection"},
            {"tier": "OPTIMAL", "time_complexity": "O(N*M)", "space_complexity": "O(N*M)", "approach_name": "BFS from Borders", "description": "BFS instead of DFS from borders; more cache-friendly, avoids stack overflow"},
        ],
    },
    {
        "slug": "non-overlapping-intervals",
        "title": "Non-overlapping Intervals",
        "difficulty": "Medium",
        "category": "Intervals",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(2^N)", "space_complexity": "O(N)", "approach_name": "Try All Subsets", "description": "Find max non-overlapping subset by checking all subsets"},
            {"tier": "BETTER", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Sort by Start + Greedy", "description": "Sort by start; greedily skip intervals that overlap"},
            {"tier": "OPTIMAL", "time_complexity": "O(N log N)", "space_complexity": "O(1)", "approach_name": "Sort by End + Greedy", "description": "Sort by end time; keep interval with earliest end â€” minimizes future conflicts"},
        ],
    },
    {
        "slug": "implement-trie-prefix-tree",
        "title": "Implement Trie (Prefix Tree)",
        "difficulty": "Medium",
        "category": "Trie",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N*L)", "space_complexity": "O(N*L)", "approach_name": "List of Strings", "description": "Store all words in a list; scan on search/startsWith"},
            {"tier": "BETTER", "time_complexity": "O(L)", "space_complexity": "O(N*L)", "approach_name": "Hash Map at Each Node", "description": "Each node has a dict of children; O(L) per operation"},
            {"tier": "OPTIMAL", "time_complexity": "O(L)", "space_complexity": "O(N*L)", "approach_name": "Array of 26 at Each Node", "description": "Fixed-size array[26] for children; O(1) child lookup vs hash collision"},
        ],
    },
    {
        "slug": "design-add-and-search-words-data-structure",
        "title": "Design Add and Search Words Data Structure",
        "difficulty": "Medium",
        "category": "Trie",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N*L)", "space_complexity": "O(N*L)", "approach_name": "List + Regex", "description": "Store words in list; use regex for wildcard search"},
            {"tier": "BETTER", "time_complexity": "O(26^L)", "space_complexity": "O(N*L)", "approach_name": "Trie + DFS", "description": "Trie for storage; DFS for '.' wildcard, try all 26 children"},
            {"tier": "OPTIMAL", "time_complexity": "O(26^L)", "space_complexity": "O(N*L)", "approach_name": "Trie + DFS Pruning", "description": "Early termination when no children match; same complexity, better constant"},
        ],
    },
    {
        "slug": "kth-smallest-element-in-a-bst",
        "title": "Kth Smallest Element in a BST",
        "difficulty": "Medium",
        "category": "Tree",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Collect All + Sort", "description": "DFS to collect all values into array, sort, return k-1 index"},
            {"tier": "BETTER", "time_complexity": "O(H+K)", "space_complexity": "O(H)", "approach_name": "Recursive Inorder", "description": "Inorder traversal (sorted order in BST); stop at kth element"},
            {"tier": "OPTIMAL", "time_complexity": "O(H+K)", "space_complexity": "O(H)", "approach_name": "Iterative Inorder (Morris-like)", "description": "Explicit stack-based inorder; no recursion overhead; O(H) space"},
        ],
    },
    {
        "slug": "construct-binary-tree-from-preorder-and-inorder-traversal",
        "title": "Construct Binary Tree from Preorder and Inorder Traversal",
        "difficulty": "Medium",
        "category": "Tree",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(N)", "approach_name": "Linear Root Search", "description": "Linear scan of inorder for root; recurse; O(N) per level"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "HashMap for Inorder Indices", "description": "Precompute valâ†’index map in inorder for O(1) root lookup"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "HashMap + Index Passing", "description": "Pass inorder bounds as indices; avoid slicing arrays"},
        ],
    },
    {
        "slug": "binary-tree-level-order-traversal",
        "title": "Binary Tree Level Order Traversal",
        "difficulty": "Medium",
        "category": "Tree",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(N)", "approach_name": "DFS with Level Tracking", "description": "DFS, track depth; append to result[depth]; rebuilds level list each time"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "BFS with Size Snapshot", "description": "BFS; at each level, dequeue exactly queue.size() nodes"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(W)", "approach_name": "BFS with Deque", "description": "Use collections.deque for O(1) popleft; W = max width (usually better space)"},
        ],
    },
    {
        "slug": "serialize-and-deserialize-binary-tree",
        "title": "Serialize and Deserialize Binary Tree",
        "difficulty": "Hard",
        "category": "Tree",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(N)", "approach_name": "Inorder+Preorder Combo", "description": "Store two traversals; reconstruct with O(NÂ²) root search"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "BFS (Level Order)", "description": "BFS serialize with null markers; BFS deserialize level by level"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "DFS Preorder + Null Markers", "description": "Preorder with null markers; deserialize with iterator consuming tokens"},
        ],
    },
    {
        "slug": "top-k-frequent-elements",
        "title": "Top K Frequent Elements",
        "difficulty": "Medium",
        "category": "Heap",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Count + Sort", "description": "Count frequencies, sort by frequency descending, take first k"},
            {"tier": "BETTER", "time_complexity": "O(N log K)", "space_complexity": "O(N)", "approach_name": "Min-Heap of size K", "description": "Maintain a min-heap of size K; push/pop as new frequencies arrive"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Bucket Sort", "description": "Bucket by frequency (max freq = N); iterate buckets from high to low"},
        ],
    },
    {
        "slug": "find-median-from-data-stream",
        "title": "Find Median from Data Stream",
        "difficulty": "Hard",
        "category": "Heap",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Sort on Each Query", "description": "Store all numbers; sort array to find median on each findMedian call"},
            {"tier": "BETTER", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Insertion Sort Maintain Sorted", "description": "Keep sorted list; binary search insert (O(N) shift), O(1) median"},
            {"tier": "OPTIMAL", "time_complexity": "O(log N) add, O(1) find", "space_complexity": "O(N)", "approach_name": "Two Heaps (Max + Min)", "description": "Max-heap for lower half, min-heap for upper half; balance sizes on insert"},
        ],
    },
    {
        "slug": "longest-common-subsequence",
        "title": "Longest Common Subsequence",
        "difficulty": "Medium",
        "category": "Dynamic Programming",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(2^(N+M))", "space_complexity": "O(N+M)", "approach_name": "Recursion", "description": "At each position: match and advance both, or skip one; exponential"},
            {"tier": "BETTER", "time_complexity": "O(N*M)", "space_complexity": "O(N*M)", "approach_name": "2D DP Table", "description": "dp[i][j] = LCS of text1[:i] and text2[:j]; fill by recurrence"},
            {"tier": "OPTIMAL", "time_complexity": "O(N*M)", "space_complexity": "O(min(N,M))", "approach_name": "1D DP Rolling Array", "description": "Only keep two rows (current and previous) â€” halves space"},
        ],
    },
    {
        "slug": "edit-distance",
        "title": "Edit Distance",
        "difficulty": "Hard",
        "category": "Dynamic Programming",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(3^(N+M))", "space_complexity": "O(N+M)", "approach_name": "Recursion", "description": "At each step: insert, delete, or replace; three recursive branches"},
            {"tier": "BETTER", "time_complexity": "O(N*M)", "space_complexity": "O(N*M)", "approach_name": "2D DP Table", "description": "dp[i][j] = min edits to convert word1[:i] to word2[:j]"},
            {"tier": "OPTIMAL", "time_complexity": "O(N*M)", "space_complexity": "O(min(N,M))", "approach_name": "1D DP Rolling Row", "description": "Only keep one row + one prev cell; same recurrence, O(min) space"},
        ],
    },
    {
        "slug": "trapping-rain-water",
        "title": "Trapping Rain Water",
        "difficulty": "Hard",
        "category": "Two Pointers",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(1)", "approach_name": "Per-Column Max Scan", "description": "For each column i: scan left for max_left, scan right for max_right"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Prefix Max Arrays", "description": "Precompute left_max[] and right_max[] arrays; water[i] = min(L,R) - height[i]"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Two Pointers", "description": "l,r pointers; if height[l]<height[r]: water += max_l - height[l]; else water += max_r - height[r]"},
        ],
    },
    {
        "slug": "sliding-window-maximum",
        "title": "Sliding Window Maximum",
        "difficulty": "Hard",
        "category": "Sliding Window",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N*K)", "space_complexity": "O(N)", "approach_name": "Scan Each Window", "description": "For each of N-K+1 windows, scan K elements for max"},
            {"tier": "BETTER", "time_complexity": "O(N log K)", "space_complexity": "O(K)", "approach_name": "Max Heap", "description": "Max-heap of size K; pop stale elements when outside window"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(K)", "approach_name": "Monotonic Deque", "description": "Deque stores indices in decreasing value order; front always has window max"},
        ],
    },
    {
        "slug": "minimum-window-substring",
        "title": "Minimum Window Substring",
        "difficulty": "Hard",
        "category": "Sliding Window",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ³)", "space_complexity": "O(N+M)", "approach_name": "All Substrings", "description": "Generate all substrings; check each contains all t chars"},
            {"tier": "BETTER", "time_complexity": "O(NÂ²)", "space_complexity": "O(N+M)", "approach_name": "Expanding Window", "description": "Expand right until valid; restart from i+1 instead of shrinking"},
            {"tier": "OPTIMAL", "time_complexity": "O(N+M)", "space_complexity": "O(N+M)", "approach_name": "Shrinkable Sliding Window", "description": "Expand right until valid; then shrink left while still valid; track min window"},
        ],
    },
    {
        "slug": "largest-rectangle-in-histogram",
        "title": "Largest Rectangle in Histogram",
        "difficulty": "Hard",
        "category": "Stack",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(1)", "approach_name": "Try All Pairs", "description": "For each pair (i,j), compute min height in range * width"},
            {"tier": "BETTER", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Divide and Conquer", "description": "Recursively find min bar; max area is either from left, right, or spans min"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Monotonic Stack", "description": "Maintain increasing stack of indices; on shorter bar, pop and compute area"},
        ],
    },
    {
        "slug": "basic-calculator",
        "title": "Basic Calculator",
        "difficulty": "Hard",
        "category": "Stack",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(N)", "approach_name": "Repeated Simplification", "description": "Repeatedly find and evaluate innermost parentheses"},
            {"tier": "BETTER", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Recursive Parser", "description": "Recursive descent parser; each level handles one paren group"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(N)", "approach_name": "Stack with Sign Tracking", "description": "Stack stores (result, sign) on open paren; apply sign on close"},
        ],
    },
    {
        "slug": "lru-cache",
        "title": "LRU Cache",
        "difficulty": "Medium",
        "category": "Design",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(N) get/put", "space_complexity": "O(N)", "approach_name": "List with Linear Search", "description": "List of (key,val); linear search for get; shift on put"},
            {"tier": "BETTER", "time_complexity": "O(N) get/put", "space_complexity": "O(N)", "approach_name": "OrderedDict", "description": "Python OrderedDict: move_to_end on access, popitem(last=False) on eviction"},
            {"tier": "OPTIMAL", "time_complexity": "O(1) get/put", "space_complexity": "O(N)", "approach_name": "HashMap + Doubly Linked List", "description": "Hash map for O(1) lookup; doubly linked list for O(1) LRU eviction"},
        ],
    },
    {
        "slug": "alien-dictionary",
        "title": "Alien Dictionary",
        "difficulty": "Hard",
        "category": "Graph",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ² * L)", "space_complexity": "O(1)", "approach_name": "Try All Orderings", "description": "Try all permutations of characters, check each against word order"},
            {"tier": "BETTER", "time_complexity": "O(N * L)", "space_complexity": "O(V+E)", "approach_name": "DFS Topological Sort", "description": "Build char dependency graph; DFS for topological order; detect cycle"},
            {"tier": "OPTIMAL", "time_complexity": "O(N * L)", "space_complexity": "O(V+E)", "approach_name": "Kahn's BFS Topo Sort", "description": "BFS from zero in-degree chars; more intuitive cycle detection via remaining nodes"},
        ],
    },
    {
        "slug": "meeting-rooms-ii",
        "title": "Meeting Rooms II",
        "difficulty": "Medium",
        "category": "Intervals",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(N)", "approach_name": "Simulate All Assignments", "description": "Try assigning each meeting to an available room; track end times"},
            {"tier": "BETTER", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Sort + Min-Heap", "description": "Sort by start; min-heap of end times; pop if room free, else add new"},
            {"tier": "OPTIMAL", "time_complexity": "O(N log N)", "space_complexity": "O(N)", "approach_name": "Two-Array Sweep Line", "description": "Separate start/end arrays; merge-sort style sweep; rooms = max concurrent starts"},
        ],
    },
    {
        "slug": "find-the-duplicate-number",
        "title": "Find the Duplicate Number",
        "difficulty": "Medium",
        "category": "Array",
        "complexity_targets": [
            {"tier": "BRUTE_FORCE", "time_complexity": "O(NÂ²)", "space_complexity": "O(1)", "approach_name": "Nested Loop", "description": "For each pair (i,j) check if nums[i]==nums[j]"},
            {"tier": "BETTER", "time_complexity": "O(N log N)", "space_complexity": "O(1)", "approach_name": "Binary Search on Value", "description": "Binary search on [1,N]: count elements â‰¤ mid; if count > mid â†’ duplicate in lower half"},
            {"tier": "OPTIMAL", "time_complexity": "O(N)", "space_complexity": "O(1)", "approach_name": "Floyd's Cycle Detection", "description": "Treat array as linked list (val = next node); find cycle entry point"},
        ],
    },
]


async def run_seed():
    from app.db.database import init_db, AsyncSessionLocal
    from app.db.crud import upsert_problem

    await init_db()
    async with AsyncSessionLocal() as session:
        count = 0
        for prob in PROBLEMS:
            await upsert_problem(session, prob)
            count += 1
        print(f"[Seed] Seeded {count} problems successfully.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_seed())

