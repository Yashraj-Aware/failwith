#!/usr/bin/env python3
"""
Demo: failwith in action — showing all major error types.
Run: python3 demo.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import failwith

failwith.install(theme="dark")

print("=" * 60)
print("  failwith demo — pick an error to see suggestions")
print("=" * 60)
print()
print("  1. ModuleNotFoundError  (cv2)")
print("  2. KeyError             (fuzzy match)")
print("  3. TypeError            (str + int)")
print("  4. FileNotFoundError    (similar files)")
print("  5. ValueError           (int conversion)")
print("  6. ZeroDivisionError    (zero var detection)")
print("  7. AttributeError       (NoneType)")
print("  8. IndexError           (out of range)")
print("  9. JSONDecodeError      (bad JSON)")
print(" 10. RecursionError       (infinite loop)")
print()

choice = input("Pick a number (1-10): ").strip()

if choice == "1":
    import cv2

elif choice == "2":
    data = {"username": "john", "email": "j@example.com", "id": 42}
    print(data["user_name"])

elif choice == "3":
    name = "Count"
    total = 42
    result = name + ": " + total

elif choice == "4":
    open("config/settigns.yaml")

elif choice == "5":
    int("forty-two")

elif choice == "6":
    users_online = 0
    total_users = 100
    ratio = total_users / users_online

elif choice == "7":
    result = None
    result.append("item")

elif choice == "8":
    items = ["apple", "banana", "cherry"]
    print(items[10])

elif choice == "9":
    import json
    json.loads('{"name": "John", "age": 30,}')

elif choice == "10":
    def process(n):
        return process(n + 1)
    process(0)

else:
    print("Invalid choice")
