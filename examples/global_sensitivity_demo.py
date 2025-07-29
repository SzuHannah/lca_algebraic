"""Minimal end-to-end workflow for global sensitivity analysis.

This demo illustrates how to:

1. create a Brightway2 compatible database,
2. assign uncertainties to 40 % of the exchanges,
3. run a Sobol based global sensitivity analysis,
4. identify the most influential exchanges,
5. parameterise them and
6. build a simplified model explaining most of the variance.

The script is deliberately short but each step is split in a dedicated
function so that it can be reused in other projects.
"""

import random
import brightway2 as bw
import lca_algebraic as agb

BG_DB = "bg"
FG_DB = "fg"


def setup_project():
    bw.projects.set_current("demo_project")
    bw.bw2setup()
    agb.resetDb(BG_DB, foreground=False)
    agb.resetDb(FG_DB, foreground=True)


def build_demo_database():
    # Biosphere flows
    co2 = agb.newActivity(BG_DB, "CO2", type="emission", unit="kg")
    ch4 = agb.newActivity(BG_DB, "CH4", type="emission", unit="kg")

    # Impact methods
    m_co2 = bw.Method(("demo", "co2", "total"))
    m_co2.register(unit="kg", description="CO2" )
    m_co2.write([(co2.key, 1.0)])

    m_ch4 = bw.Method(("demo", "ch4", "total"))
    m_ch4.register(unit="kg", description="CH4" )
    m_ch4.write([(ch4.key, 1.0)])

    # Background activities
    bg1 = agb.newActivity(BG_DB, "bg1", "kg", {co2: 1})
    bg2 = agb.newActivity(BG_DB, "bg2", "kg", {ch4: 1})

    # Foreground activities
    fg1 = agb.newActivity(FG_DB, "fg1", "kg", {bg1: 2, bg2: 3})
    fg2 = agb.newActivity(FG_DB, "fg2", "kg", {bg1: 1, bg2: 1})

    root = agb.newActivity(FG_DB, "root", "kg", {fg1: 1, fg2: 1})
    return root, [m_co2.key, m_ch4.key]


def add_exchange_uncertainty(db_name, percent=0.4):
    db = bw.Database(db_name)
    exchs = [exc for act in db for exc in act.exchanges() if exc["type"] != "production"]
    n_uncertain = max(1, int(len(exchs) * percent))
    selected = random.sample(exchs, n_uncertain)
    for exc in selected:
        val = exc["amount"]
        param = agb.newFloatParam(
            f"p_{exc['input'][1]}",
            default=val,
            min=0.5 * val,
            max=1.5 * val,
            distrib=agb.params.DistributionType.TRIANGLE,
        )
        exc["amount"] = param


def run_gsa(model, methods, n=200):
    return agb.sobol_simplify_model(model, methods, n=n)


def print_top_parameters(simplified):
    """Display sorted Sobol indices for each impact method."""
    for i, lambd in enumerate(simplified):
        print(f"Impact {i}")
        for name, s1 in sorted(lambd.sobols.items(), key=lambda x: -x[1]):
            print(f"  {name}: {s1:.3f}")


def main():
    setup_project()
    model, methods = build_demo_database()
    add_exchange_uncertainty(FG_DB, percent=0.4)

    # Compute sensitivity and simplified model
    simplified = run_gsa(model, methods, n=500)
    print_top_parameters(simplified)
    agb.compare_simplified(model, methods, simplified)

if __name__ == "__main__":
    main()
