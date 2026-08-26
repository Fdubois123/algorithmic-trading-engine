<div align="center">

# ◈ ALGORITHMIC TRADING ENGINE

### Regime-Adaptive Quantitative Research • Portfolio Intelligence • Systematic Execution

**A deterministic quantitative research framework for multi-strategy convergence across changing financial market regimes.**

<br>

![Python](https://img.shields.io/badge/Python-3.13-111827?style=for-the-badge&logo=python)
![Tests](https://img.shields.io/badge/Tests-1330%20Passing-00C896?style=for-the-badge)
![Coverage](https://img.shields.io/badge/Coverage-95.76%25-00C896?style=for-the-badge)
![Ruff](https://img.shields.io/badge/Ruff-Passing-111827?style=for-the-badge)
![Release](https://img.shields.io/badge/Target-v1.0.0-0A84FF?style=for-the-badge)

<br>

> **Detect the market. Adapt the allocation. Control the risk. Preserve causality.**

</div>

---

## ◆ Executive Overview

The **Algorithmic Trading Engine** is a research-oriented quantitative trading framework designed for systematic strategy development, adaptive allocation, market-regime modelling, portfolio construction, statistical arbitrage, backtesting, execution modelling, performance analytics, and reproducible experimentation.

The framework is built around a central research question:

> **Can a diversified set of quantitative strategies dynamically converge toward more appropriate allocations as market regimes change?**

Instead of assuming that one strategy remains effective across all environments, the system detects changes in market behaviour and dynamically alters exposure across multiple quantitative strategies.

The engine currently supports:

- systematic market indicators,
- trend and momentum strategies,
- mean-reversion strategies,
- volatility strategies,
- statistical arbitrage,
- portfolio optimization,
- risk parity,
- Black-Litterman allocation,
- market-regime detection,
- adaptive strategy allocation,
- turnover constraints,
- transaction-cost modelling,
- causal walk-forward convergence,
- benchmark comparison,
- strategy and regime attribution,
- research reporting,
- experiment serialization,
- deterministic experiment identities,
- SHA-256 artifact verification,
- command-line execution.

---

# ◇ SYSTEM STATUS

| Metric | Current State |
|---|---:|
| Automated tests | **1,330 passing** |
| Total coverage | **95.76%** |
| Required coverage | **≥ 95.00%** |
| Branch coverage | Enabled |
| Static analysis | Ruff |
| Formatting | Ruff Format |
| Public API tests | Passing |
| Production CLI tests | Passing |
| End-to-end tests | Passing |
| Artifact integrity | SHA-256 |
| Release target | **v1.0.0** |

The v1.0 development process uses a strict release gate:

```text
TESTS       → PASS
COVERAGE    → ≥ 95%
RUFF        → PASS
FORMAT      → PASS
PUBLIC API  → PASS
E2E         → PASS
ARTIFACTS   → VERIFIED