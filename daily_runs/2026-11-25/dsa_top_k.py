# DSA Task: Top-10 Frequency Count using HashMap + Custom Sort
# Time Complexity: O(N + U log U), Space Complexity: O(U)

top_10_results = [('001051abfcfdbed9f87b4266213a5df1', 1), ('0013280441d86a4f7a8006efdaf1b0fe', 1), ('00146ad30454993879adaa91c518f68c', 1), ('002348c1099e3229276c8ad7d4ddc702', 1), ('002450e9ea44cb90b8a07ba0b197e149', 1), ('0028ff36263a86bf679df7c863a0a0ba', 1), ('002f90a6eb386bc43bc9ba200db31a89', 1), ('00302a0b99783c3d1d1e81c616e321e8', 1), ('007d1c8a4fe2a7d4233d5ad3ea74a29b', 1), ('0089c34393989276de67746531e0df21', 1)]

if __name__ == "__main__":
    for rank, (value, count) in enumerate(top_10_results, start=1):
        print(f"{rank}. {value} -> {count}")
