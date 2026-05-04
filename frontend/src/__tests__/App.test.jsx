import { render, screen } from '@testing-library/react'

// vi.mock() is HOISTED to the top of the file by Vitest before any imports
// run, so even though the import below seems to come first, the mock is
// already in place when App.jsx imports useAuth.
vi.mock('react-oidc-context', () => ({
  useAuth: () => ({
    isLoading: false,
    isAuthenticated: false,
    user: null,
    signinRedirect: vi.fn(),
    signoutRedirect: vi.fn(),
  }),
}))

import App from '../App'

describe('App (unauthenticated)', () => {
  it('renders the Sign in button', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders the Try Demo button', () => {
    render(<App />)
    expect(screen.getByRole('button', { name: /try demo/i })).toBeInTheDocument()
  })
})
