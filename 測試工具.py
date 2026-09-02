import sys, statistics as s
nums = list(map(float, sys.argv[1:]))
print(f"Mean: {s.mean(nums)}, Mode: {s.mode(nums)}")