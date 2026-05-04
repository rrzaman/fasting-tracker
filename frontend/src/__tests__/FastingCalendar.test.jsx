import { act, render, screen } from '@testing-library/react'

import FastingCalendar from '../components/FastingCalendar'

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

// FastingCalendar fires a fetch + setState in useEffect on mount. Wrap
// each render in act(async) so React flushes those updates before the test.
async function renderCalendar(props) {
  let result
  await act(async () => {
    result = render(<FastingCalendar {...props} />)
  })
  return result
}

describe('FastingCalendar', () => {
  it('renders the loading skeleton when loading is true', async () => {
    const { container } = await renderCalendar({
      fastingData: {},
      healthDates: new Set(),
      loading: true,
      onDateClick: vi.fn(),
    })
    // The skeleton wraps everything in <div className="skeleton-root">.
    // Targeting the wrapper is more stable than asserting on internal structure.
    expect(container.querySelector('.skeleton-root')).not.toBeNull()
  })

  it('renders the current month name and year in the header', async () => {
    await renderCalendar({
      fastingData: {},
      healthDates: new Set(),
      loading: false,
      onDateClick: vi.fn(),
    })

    // Component reads new Date() on mount, so we check that a month name
    // appears as a heading. This avoids freezing time while still verifying
    // the header renders correctly.
    const heading = screen.getByRole('heading', { level: 2 })
    const monthFound = MONTHS.some(m => heading.textContent.includes(m))
    expect(monthFound).toBe(true)
    expect(heading.textContent).toMatch(/\d{4}/) // year (4 digits)
  })
})
