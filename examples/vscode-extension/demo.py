"""
Character Prefix Code Completion Demo

This file demonstrates how to use the Character Prefix Code Completion extension
with both OpenAI and Gemini models.

Instructions:
1. Position your cursor at the end of a line with '# Complete:'
2. Press Ctrl+Shift+P to open the command palette
3. Type 'Character Prefix' and select 'Character Prefix: Complete with Prefix'
4. Enter the suggested character prefix 
5. See the magic happen!

You can switch between models with:
  Ctrl+Shift+P > Character Prefix: Switch Model Type
"""

# DEMO 1: Basic Function with OpenAI
# Complete: def factorial(n):
# Suggested prefix: "def factorial(n):"

# DEMO 2: Class with Gemini
# Complete: class BinaryTree:
# Suggested prefix: "class BinaryTree:"

# DEMO 3: List Comprehension
# Complete: squares = [x*x for 
# Suggested prefix: "[x*x for "

# DEMO 4: Complex Function
# Complete: def quick_sort(arr):
# Suggested prefix: "def quick_sort(arr):"

# DEMO 5: Context-Aware Completion
import numpy as np
import pandas as pd

# Now try completing this with both OpenAI and Gemini:
# Complete: def analyze_dataset(
# Suggested prefix: "def analyze_dataset(" 