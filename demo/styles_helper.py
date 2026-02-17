"""Generate a composite image showing all chart types for a given matplotlib style.

Usage:
    python demo/styles_helper.py STYLE_NAME [-o OUTPUT_PATH]

Produces a single wide image with bar, line, scatter, pie, histogram, and radar
subplots side by side, all rendered in the specified style.
"""

import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


# Sample data shared across chart types
BAR_DATA = {"categories": ["A", "B", "C", "D", "E"], "values": [42, 28, 35, 51, 19]}
LINE_DATA = {
    "x": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    "y1": [100, 120, 115, 140, 160, 155],
    "y2": [80, 90, 85, 95, 100, 110],
}
SCATTER_DATA = {
    "x": [1.2, 2.5, 3.1, 4.7, 5.3, 6.0, 7.2, 8.5, 9.1, 10.0],
    "y": [2.4, 4.1, 3.8, 6.2, 5.9, 7.8, 8.1, 9.3, 10.2, 11.5],
}
PIE_DATA = {"labels": ["Rent", "Food", "Transport", "Fun", "Other"], "sizes": [40, 20, 15, 15, 10]}
HIST_DATA = [72, 85, 91, 78, 88, 95, 67, 82, 90, 76, 89, 93, 71, 84, 87, 92, 79, 86, 94, 81]
RADAR_DATA = {
    "labels": ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
    "fighter": [18, 14, 16, 10, 12, 8],
    "wizard": [8, 12, 10, 18, 14, 16],
}


def generate_style_image(style_name: str, output_path: str):
    """Create a composite image with 6 chart types in the given style."""
    with plt.style.context(style_name):
        fig = plt.figure(figsize=(30, 4.5))
        axes = [fig.add_subplot(1, 6, i + 1) for i in range(5)]
        axes.append(fig.add_subplot(1, 6, 6, polar=True))

        # Bar chart
        ax = axes[0]
        ax.bar(BAR_DATA["categories"], BAR_DATA["values"])
        ax.set_title("Bar")

        # Line chart
        ax = axes[1]
        x_pos = range(len(LINE_DATA["x"]))
        ax.plot(x_pos, LINE_DATA["y1"], marker="o", label="revenue")
        ax.plot(x_pos, LINE_DATA["y2"], marker="o", label="costs")
        ax.set_xticks(list(x_pos))
        ax.set_xticklabels(LINE_DATA["x"])
        ax.legend(fontsize=8)
        ax.set_title("Line")

        # Scatter plot
        ax = axes[2]
        ax.scatter(SCATTER_DATA["x"], SCATTER_DATA["y"])
        ax.set_title("Scatter")

        # Pie chart
        ax = axes[3]
        ax.pie(PIE_DATA["sizes"], labels=PIE_DATA["labels"], autopct="%1.0f%%", textprops={"fontsize": 8})
        ax.set_title("Pie")

        # Histogram
        ax = axes[4]
        ax.hist(HIST_DATA, bins=8)
        ax.set_title("Histogram")

        # Radar chart
        ax = axes[5]
        angles = np.linspace(0, 2 * np.pi, len(RADAR_DATA["labels"]), endpoint=False).tolist()
        angles_closed = angles + [angles[0]]
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_thetagrids(np.degrees(angles), RADAR_DATA["labels"], fontsize=7)
        for series, name in [(RADAR_DATA["fighter"], "fighter"), (RADAR_DATA["wizard"], "wizard")]:
            values = series + [series[0]]
            ax.plot(angles_closed, values, marker="o", label=name)
            ax.fill(angles_closed, values, alpha=0.25)
        ax.legend(fontsize=7, loc="upper right", bbox_to_anchor=(1.3, 1.1))
        ax.set_title("Radar")

        fig.suptitle(style_name, fontsize=16, fontweight="bold")
        fig.tight_layout()
        fig.savefig(output_path, dpi=80)
        plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a style sampler image")
    parser.add_argument("style", help="Matplotlib style name")
    parser.add_argument("-o", "--output", default=None, help="Output file path")
    args = parser.parse_args()

    output = args.output or f"{args.style}.png"
    generate_style_image(args.style, output)
    print(output)
