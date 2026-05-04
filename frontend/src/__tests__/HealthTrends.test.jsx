import { render } from '@testing-library/react'

import HealthTrends from '../components/HealthTrends'

describe('HealthTrends', () => {
  it('renders the loading skeleton when loading is true', () => {
    const { container } = render(
      <HealthTrends
        healthData={[]}
        fastingData={{}}
        loading={true}
        focusDate={null}
        clearFocus={vi.fn()}
      />
    )
    expect(container.querySelector('.skeleton-root')).not.toBeNull()
  })
})
