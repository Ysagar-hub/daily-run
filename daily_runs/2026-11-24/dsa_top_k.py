# DSA Task: Top-10 Frequency Count using HashMap + Custom Sort
# Time Complexity: O(N + U log U), Space Complexity: O(U)

top_10_results = [('s1', 1), ('s10', 1), ('s100', 1), ('s1000', 1), ('s1001', 1), ('s1002', 1), ('s1003', 1), ('s1004', 1), ('s1005', 1), ('s1006', 1)]

if __name__ == "__main__":
    for rank, (value, count) in enumerate(top_10_results, start=1):
        print(f"{rank}. {value} -> {count}")
