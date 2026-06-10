// Statistical helpers used by HealthTrends.
// Pure functions — no React, no DOM — so they can be unit-tested in isolation.

export const mean = arr => arr.reduce((s, v) => s + v, 0) / arr.length

// Bessel-corrected sample variance (divides by n - 1).
export const variance = arr => {
    const m = mean(arr)
    return arr.reduce((s, v) => s + (v - m) ** 2, 0) / (arr.length - 1)
}

export function pearson(a, b) {
    const ma = mean(a), mb = mean(b)
    const num = a.reduce((s, v, i) => s + (v - ma) * (b[i] - mb), 0)
    const den = Math.sqrt(
        a.reduce((s, v) => s + (v - ma) ** 2, 0) *
        b.reduce((s, v) => s + (v - mb) ** 2, 0)
    )
    return den === 0 ? 0 : num / den
}

// Correlation between x and y controlling for z.
// r_xy.z = (r_xy - r_xz * r_yz) / sqrt((1 - r_xz²)(1 - r_yz²))
export function partialCorrelation(x, y, z) {
    if (x.length < 5) return null
    const rxy = pearson(x, y)
    const rxz = pearson(x, z)
    const ryz = pearson(y, z)
    const num = rxy - rxz * ryz
    const den = Math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    return den === 0 ? null : num / den
}

// Cohen's d using pooled standard deviation:
// d = (mean(a) - mean(b)) / sqrt(((na-1)*var(a) + (nb-1)*var(b)) / (na+nb-2))
export function cohensD(a, b) {
    const na = a.length, nb = b.length
    if (na < 2 || nb < 2) return null
    const pooledVar = ((na - 1) * variance(a) + (nb - 1) * variance(b)) / (na + nb - 2)
    if (pooledVar <= 0) return 0
    return (mean(a) - mean(b)) / Math.sqrt(pooledVar)
}

// Cohen's conventional thresholds for interpreting |d|.
export function effectSizeLabel(d) {
    const abs = Math.abs(d)
    if (abs < 0.2) return 'negligible'
    if (abs < 0.5) return 'small'
    if (abs < 0.8) return 'medium'
    return 'large'
}

// Welch's two-sample t-test (unequal variances).
// Returns { t, df, p } where p is the two-tailed p-value.
export function welchTTest(a, b) {
    const na = a.length, nb = b.length
    if (na < 2 || nb < 2) return null
    const va = variance(a), vb = variance(b)
    const seSq = va / na + vb / nb
    if (seSq <= 0) return { t: 0, df: na + nb - 2, p: 1 }
    const t = (mean(a) - mean(b)) / Math.sqrt(seSq)
    // Welch–Satterthwaite degrees of freedom
    const df = (seSq ** 2) / (((va / na) ** 2) / (na - 1) + ((vb / nb) ** 2) / (nb - 1))
    const p = tCdfTwoTailed(t, df)
    return { t, df, p }
}

// Two-tailed p-value from Student's t-distribution.
// Uses the identity: p = I_x(df/2, 1/2) where x = df / (df + t²),
// and I_x is the regularized incomplete beta function.
export function tCdfTwoTailed(t, df) {
    if (df <= 0) return NaN
    const x = df / (df + t * t)
    return regularizedIncompleteBeta(x, df / 2, 0.5)
}

// --- Numerical helpers (Numerical Recipes recipes, ported to JS) ---

// Lanczos approximation of log(Γ(x)). Coefficients are standard Numerical
// Recipes values; sub-ULP rounding is expected and inconsequential.
/* eslint-disable no-loss-of-precision */
function logGamma(x) {
    const cof = [
        76.18009172947146, -86.50532032941677, 24.01409824083091,
        -1.231739572450155, 1.208650973866179e-3, -5.395239384953e-6,
    ]
    let y = x
    const tmp = x + 5.5 - (x + 0.5) * Math.log(x + 5.5)
    let ser = 1.000000000190015
    for (let j = 0; j < 6; j++) ser += cof[j] / ++y
    return -tmp + Math.log(2.5066282746310005 * ser / x)
}
/* eslint-enable no-loss-of-precision */

// Continued-fraction expansion for the incomplete beta function (Lentz method).
function betacf(x, a, b) {
    const MAXITER = 200
    const EPS = 3e-7
    const FPMIN = 1e-30
    const qab = a + b, qap = a + 1, qam = a - 1
    let c = 1
    let d = 1 - qab * x / qap
    if (Math.abs(d) < FPMIN) d = FPMIN
    d = 1 / d
    let h = d
    for (let m = 1; m <= MAXITER; m++) {
        const m2 = 2 * m
        let aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN
        c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN
        d = 1 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d; if (Math.abs(d) < FPMIN) d = FPMIN
        c = 1 + aa / c; if (Math.abs(c) < FPMIN) c = FPMIN
        d = 1 / d
        const del = d * c
        h *= del
        if (Math.abs(del - 1) < EPS) return h
    }
    return h
}

// Regularized incomplete beta function I_x(a, b).
function regularizedIncompleteBeta(x, a, b) {
    if (x <= 0) return 0
    if (x >= 1) return 1
    const bt = Math.exp(
        logGamma(a + b) - logGamma(a) - logGamma(b)
        + a * Math.log(x) + b * Math.log(1 - x)
    )
    return x < (a + 1) / (a + b + 2)
        ? bt * betacf(x, a, b) / a
        : 1 - bt * betacf(1 - x, b, a) / b
}
