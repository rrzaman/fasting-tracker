import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import DemoBanner from '../components/DemoBanner'

describe('DemoBanner', () => {
  it('renders the demo mode message', () => {
    render(<DemoBanner onExit={vi.fn()} />)
    // getByText takes a string or regex. Regex with /i is case-insensitive.
    expect(screen.getByText(/demo mode/i)).toBeInTheDocument()
  })

  it('renders an Exit Demo button', () => {
    render(<DemoBanner onExit={vi.fn()} />)
    // getByRole('button', { name: ... }) is the preferred query. It matches
    // how a screen reader (and a real user) would find the button.
    expect(screen.getByRole('button', { name: /exit demo/i })).toBeInTheDocument()
  })

  it('calls onExit when the button is clicked', async () => {
    const onExit = vi.fn()
    const user = userEvent.setup()
    render(<DemoBanner onExit={onExit} />)

    await user.click(screen.getByRole('button', { name: /exit demo/i }))

    expect(onExit).toHaveBeenCalledTimes(1)
  })
})
