from tabulate import tabulate

def pretty_print_table(data):
  table_str = tabulate(
    data,
    headers="keys",
    tablefmt="psql",
    floatfmt=",.2f",
    intfmt=",d",
    showindex=False,
  )
  print(table_str)
