"""
Script for generating Jensen's Inequality visualization
Location: _posts/_scripts/jensen_inequality/generate_jensen_plot.py
Associated post: 2025-03-01-jensen-inequality.md
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import os

# Set style for better visualization
plt.style.use('bmh')  # Using 'bmh' style instead of seaborn
plt.figure(figsize=(10, 6))

# Define the convex function (using x^2 as example)
def convex_function(x):
    return x**2

# Generate points for the curve
x = np.linspace(-2, 2, 1000)
y = convex_function(x)

# Plot the convex function
plt.plot(x, y, 'b-', label=r'$\varphi(x) = x^2$', linewidth=2)

# Choose two points to demonstrate the inequality
x1, x2 = -1.5, 1.5
y1, y2 = convex_function(x1), convex_function(x2)

# Calculate the expected value point
x_avg = (x1 + x2) / 2
y_avg = convex_function(x_avg)
y_line_avg = (y1 + y2) / 2

# Plot the points and connecting line
plt.plot([x1, x2], [y1, y2], 'r-', label='Line segment', linewidth=2)
plt.plot([x1, x2], [y1, y2], 'ko', label=r'Points $(x_1, \varphi(x_1))$ and $(x_2, \varphi(x_2))$')
plt.plot(x_avg, y_avg, 'go', label=r'$\varphi(\mathbb{E}[X])$', markersize=8)
plt.plot(x_avg, y_line_avg, 'mo', label=r'$\mathbb{E}[\varphi(X)]$', markersize=8)

# Draw vertical lines to show the inequality
plt.vlines(x_avg, y_avg, y_line_avg, 'gray', linestyles='--')

# Add annotations
plt.annotate(r'$\varphi(\mathbb{E}[X])$', xy=(x_avg, y_avg), xytext=(x_avg+0.2, y_avg-0.5),
            arrowprops=dict(facecolor='black', shrink=0.05))
plt.annotate(r'$\mathbb{E}[\varphi(X)]$', xy=(x_avg, y_line_avg), xytext=(x_avg+0.2, y_line_avg+0.5),
            arrowprops=dict(facecolor='black', shrink=0.05))

# Customize the plot
plt.grid(True, alpha=0.3)
plt.title("Jensen's Inequality Visualization", fontsize=14, pad=20)
plt.xlabel('x', fontsize=12)
plt.ylabel(r'$\varphi(x)$', fontsize=12)
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)

# Adjust layout to prevent label cutoff
plt.tight_layout()

# Get the path to the project root (3 levels up from the script location)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
output_path = os.path.join(project_root, 'images', 'blogs', 'jensen_inequality.png')

# Create the output directory if it doesn't exist
os.makedirs(os.path.dirname(output_path), exist_ok=True)

# Save the plot
plt.savefig(output_path, dpi=300, bbox_inches='tight')
plt.close()