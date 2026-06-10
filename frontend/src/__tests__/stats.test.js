import { describe, it, expect } from 'vitest'
import {
    mean,
    variance,
    pearson,
    partialCorrelation,
    cohensD,
    effectSizeLabel,
    welchTTest,
    tCdfTwoTailed,
} from '../lib/stats'

const close = (actual, expected, tol = 1e-3) =>
    expect(Math.abs(actual - expected)).toBeLessThan(tol)

describe('mean', () => {
    it('handles a single value', () => expect(mean([5])).toBe(5))
    it('handles two values', () => expect(mean([2, 4])).toBe(3))
    it('handles negatives', () => expect(mean([-1, 0, 1])).toBe(0))
})

describe('variance (Bessel-corrected)', () => {
    it('matches the standard formula for [1, 2, 3]', () => {
        close(variance([1, 2, 3]), 1.0)
    })
    it('matches the standard formula for [2, 4, 4, 4, 5, 5, 7, 9]', () => {
        close(variance([2, 4, 4, 4, 5, 5, 7, 9]), 4.5714, 1e-3)
    })
})

describe('pearson', () => {
    it('returns 1 for perfectly correlated inputs', () => {
        close(pearson([1, 2, 3, 4], [2, 4, 6, 8]), 1.0)
    })
    it('returns -1 for perfectly anti-correlated inputs', () => {
        close(pearson([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
    })
})

describe('partialCorrelation', () => {
    it('returns null for n < 5', () => {
        expect(partialCorrelation([1, 2], [3, 4], [5, 6])).toBeNull()
    })
})

describe('cohensD', () => {
    // scipy reference: cohend with pooled SD for these arrays is approximately ±1.2649
    it('matches the textbook reference for [1..5] vs [3..7]', () => {
        close(cohensD([1, 2, 3, 4, 5], [3, 4, 5, 6, 7]), -1.2649, 1e-3)
    })
    it('is sign-flipped when arguments swap', () => {
        const a = [1, 2, 3, 4, 5], b = [3, 4, 5, 6, 7]
        close(cohensD(a, b), -cohensD(b, a))
    })
    it('returns 0 for identical groups', () => {
        expect(cohensD([1, 2, 3], [1, 2, 3])).toBe(0)
    })
    it('returns null when either group has < 2 values', () => {
        expect(cohensD([1], [1, 2, 3])).toBeNull()
    })
})

describe('effectSizeLabel', () => {
    it('labels |d| < 0.2 as negligible', () => {
        expect(effectSizeLabel(0.0)).toBe('negligible')
        expect(effectSizeLabel(0.19)).toBe('negligible')
        expect(effectSizeLabel(-0.19)).toBe('negligible')
    })
    it('labels 0.2 ≤ |d| < 0.5 as small', () => {
        expect(effectSizeLabel(0.2)).toBe('small')
        expect(effectSizeLabel(0.49)).toBe('small')
    })
    it('labels 0.5 ≤ |d| < 0.8 as medium', () => {
        expect(effectSizeLabel(0.5)).toBe('medium')
        expect(effectSizeLabel(0.79)).toBe('medium')
    })
    it('labels |d| ≥ 0.8 as large', () => {
        expect(effectSizeLabel(0.8)).toBe('large')
        expect(effectSizeLabel(2.0)).toBe('large')
        expect(effectSizeLabel(-1.5)).toBe('large')
    })
})

describe('welchTTest', () => {
    // scipy.stats.ttest_ind([1,2,3,4,5], [3,4,5,6,7], equal_var=False)
    //   → statistic ≈ -2.0, df = 8, pvalue ≈ 0.0805
    it('matches scipy for [1..5] vs [3..7]', () => {
        const { t, df, p } = welchTTest([1, 2, 3, 4, 5], [3, 4, 5, 6, 7])
        close(t, -2.0, 1e-6)
        close(df, 8.0, 1e-6)
        close(p, 0.0805, 1e-3)
    })
    it('is symmetric in p when arguments swap', () => {
        const a = [1, 2, 3, 4, 5], b = [3, 4, 5, 6, 7]
        close(welchTTest(a, b).p, welchTTest(b, a).p)
    })
    it('returns p ≈ 1 for identical groups', () => {
        const { p } = welchTTest([1, 2, 3, 4], [1, 2, 3, 4])
        close(p, 1.0, 1e-6)
    })
    it('returns null for groups with < 2 values', () => {
        expect(welchTTest([1], [1, 2, 3])).toBeNull()
    })
})

describe('tCdfTwoTailed', () => {
    it('returns 1 at t = 0', () => {
        close(tCdfTwoTailed(0, 10), 1.0, 1e-6)
    })
    it('approaches normal at large df: p(t=1.96, df=10000) ≈ 0.05', () => {
        close(tCdfTwoTailed(1.96, 10000), 0.05, 1e-3)
    })
    it('is symmetric in sign of t', () => {
        close(tCdfTwoTailed(2.0, 8), tCdfTwoTailed(-2.0, 8))
    })
})
