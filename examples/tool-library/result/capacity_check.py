"""Conditional workload arithmetic, not a queueing simulation or measured result."""

from pathlib import Path


def main():
    arrivals = 10
    interval_minutes = 30
    transaction_minutes = 3
    transactions_per_arrival = 1
    work = arrivals * transactions_per_arrival * transaction_minutes
    load = work / interval_minutes
    capacity_per_hour = 60 / transaction_minutes
    lines = [
        "Conditional capacity check",
        "Input basis: ../input.md. Ten arrivals in 30 minutes and three minutes per",
        "loan/return are volunteer recollections, not measurements.",
        "Baseline assumption: one transaction per arrival and one continuously available volunteer.",
        f"Recalled peak arrival rate: {arrivals / interval_minutes * 60:g} arrivals/hour.",
        f"Required work: {arrivals} x {transactions_per_arrival} x {transaction_minutes} = {work} volunteer-minutes in {interval_minutes} minutes.",
        f"Nominal utilization: {load:.0%}.",
        f"Nominal capacity: {capacity_per_hour:g} transactions/hour; {capacity_per_hour * 2:g} transactions in two hours.",
        "This leaves no nominal time margin for interruptions or reconciliation.",
        "Forty members does not imply forty transactions in an opening window.",
        "",
        "Illustrative sensitivity (hypothetical inputs, not candidate performance predictions):",
        "minutes/transaction | transactions/arrival | work minutes/30 minutes | nominal load",
    ]
    for minutes, per_arrival in [(2, 1), (3, 1), (4, 1), (3, 2)]:
        workload = arrivals * per_arrival * minutes
        lines.append(f"{minutes:19} | {per_arrival:20} | {workload:23} | {workload / interval_minutes:12.0%}")
    lines += [
        "",
        "Loads above 100% exceed the interval's service capacity; loads below 100%",
        "still do not predict waiting, because arrival timing and service variability matter.",
        "No expected wait, acceptable-wait threshold, or candidate speed improvement is inferred.",
        "A utilization of 100% is a headroom concern, not proof of observed overload.",
        "The steady-state queue assumptions needed for a wait formula have not been established.",
        "",
        "Checks run: exact arithmetic assertions for recalled baseline and sensitivity rows.",
    ]
    assert work == 30 and load == 1
    assert capacity_per_hour == 20 and capacity_per_hour * 2 == 40
    assert [arrivals * t * s for s, t in [(2, 1), (3, 1), (4, 1), (3, 2)]] == [20, 30, 40, 60]
    lines.append("Result: PASS. This verifies arithmetic only, not the recalled inputs or feasibility.")
    report = "\n".join(lines) + "\n"
    Path(__file__).with_name("capacity-check.txt").write_text(report, encoding="utf-8", newline="\n")
    print(report, end="")


if __name__ == "__main__":
    main()
