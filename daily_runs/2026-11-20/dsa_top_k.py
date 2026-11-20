# DSA Task: Top-10 Frequency Count using HashMap + Custom Sort
# Time Complexity: O(N + U log U), Space Complexity: O(U)

top_10_results = [('0', 1), ('1', 1), ('10', 1), ('100', 1), ('1000', 1), ('1001', 1), ('1002', 1), ('1003', 1), ('1004', 1), ('1005', 1)]

if __name__ == "__main__":
    for rank, (value, count) in enumerate(top_10_results, start=1):
        print(f"{rank}. {value} -> {count}")
