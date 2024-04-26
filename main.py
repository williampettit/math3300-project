# disable specific deprecation warning that is not relevant to this code
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# library imports
from termcolor import cprint, colored as col
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy

# our own code
from config import budget, constraints
from utilities import pretty_print_table

#
# main
#

# read data file with each platform's cpm
df = pd.read_csv("dataset/cpm.csv")
df["min_dollars"].fillna(0, inplace=True)

# cost vector to maximize total impressions
# (since linprog minimizes by default, use negative to simulate maximization)
c = [ -1_000 ] * len(df)

# coefficients for budget constraint
A = [ df["cpm"].values ] # upper bound matrix for budget constraint
b = [ budget ]           # upper bound vector for budget constraint

# convert constraints into lower/upper bounds, with respect to min dollar spend per platform
bounds = []
for platform in df["platform"]:
  cpm = df[df["platform"] == platform]["cpm"].values[0]
  min_dollars = df[df["platform"] == platform]["min_dollars"].values[0]
  (lower, upper) = constraints[platform]
  lower = max(lower, min_dollars / cpm)
  bounds.append((lower, upper))

# find optimal number of impressions to buy on each platform
print(f"\nOptimizing impressions across {len(df['platform'])} platform(s) with a budget of ${budget:,.2f}...")
result = scipy.optimize.linprog(
  c,                # cost vector
  A_ub=A,           # upper bound matrix for budget constraint
  b_ub=b,           # upper bound vector for budget constraint
  bounds=bounds,    # lower/upper bounds for each platform
  method="simplex", # (use simplex method)
)

# handle failure
if not result.success:
  cprint(f"\nOptimization failed: {result.message}", color="red")
  exit()

#
# visualize results
#

cprint("\nOptimization was successful.", color="green")

# create dataframe with optimal number of impressions to buy for each platform
optimal_df = pd.DataFrame(columns = ["platform", "impressions", "cost", "percent"])

# add platform names and optimal number of impressions to dataframe
for (platform, impressions) in zip(df["platform"], result.x):
  # convert back to actual number of impressions
  impressions = int(impressions) * 1_000

  # calculate cost
  cost = df[df["platform"] == platform]["cpm"].values[0] * impressions

  # convert cost to thousands of dollars
  cost = cost / 1_000.0

  # calculate percent of budget spent
  percent = (cost / budget) * 100.0

  # add row to dataframe
  optimal_df.loc[len(optimal_df)] = [platform, impressions, cost, percent]

# print optimal number of impressions to buy for each platform
print("\nOptimal number of impressions to buy per platform:")
pretty_print_table(optimal_df)

# print total impressions
total_impressions = optimal_df["impressions"].sum()
print("\nTotal impressions:", col(f"{total_impressions:,d}", "cyan"))

# print total cost
total_cost = optimal_df["cost"].sum()
print("Total cost:       ", col(f"${total_cost:,.2f}", "cyan"))
print()

#
# create pie chart of optimal number of impressions to buy for each platform
#

(fig, ax) = plt.subplots(figsize=(10, 8), subplot_kw=dict(aspect="equal"))

platforms = optimal_df["platform"]
data = optimal_df["impressions"]

def func(pct, allvals):
  absolute = np.round(pct / 100.0 * np.sum(allvals))
  ret = f"{pct:.1f}%\n({absolute:,.0f})"
  print(ret)
  return ret

(wedges, texts, autotexts) = ax.pie(
  data,
  autopct=lambda pct: func(pct, data),
  textprops=dict(color="w"),
  colors=mcolors.TABLEAU_COLORS, # type: ignore
)

wedges[0].properties

ax.legend(
  wedges, platforms,
  title="Platforms",
  loc="center left",
  bbox_to_anchor=(1.0, 0.0, 0.5, 1.0),
)

plt.setp(
  autotexts,
  size=8,
)

ax.set_title("Optimal Impressions to Buy / Platform", fontweight="bold")

plt.savefig("output.png", dpi=300)

plt.show()
