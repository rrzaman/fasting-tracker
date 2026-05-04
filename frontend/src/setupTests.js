// Runs once before each test file. Configures the global test environment.

// Adds matchers like .toBeInTheDocument(), .toHaveTextContent(), etc.
import '@testing-library/jest-dom/vitest'

import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  // Unmounts the rendered component and clears the JSDOM body between tests.
  // Without this, tests would leak DOM nodes into each other.
  cleanup()
  // Restores any vi.spyOn / vi.fn that a test set up. vi.mock() is unaffected.
  vi.restoreAllMocks()
})

// FastingCalendar fetches Aladhan in a useEffect on mount. Without this stub
// every test that renders the component would hit the real network. Tests
// that need to assert on fetch behaviour can override this with vi.fn().
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ data: [] }),
  })
)
