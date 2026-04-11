import { render, screen, fireEvent } from '@testing-library/react'
import TextAreaWithCounter from './TextAreaWithCounter'

describe('TextAreaWithCounter', () => {
  const defaultProps = {
    value: '',
    onChange: vi.fn(),
    label: 'Resume text',
    maxLength: 1000,
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders label', () => {
    render(<TextAreaWithCounter {...defaultProps} />)
    expect(screen.getByText('Resume text')).toBeInTheDocument()
  })

  it('shows character count', () => {
    render(<TextAreaWithCounter {...defaultProps} value="hello" />)
    expect(screen.getByText('5 / 1,000')).toBeInTheDocument()
  })

  it('calls onChange when typing', () => {
    render(<TextAreaWithCounter {...defaultProps} />)
    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'new text' } })
    expect(defaultProps.onChange).toHaveBeenCalledWith('new text')
  })

  it('shows over-limit warning', () => {
    const longText = 'x'.repeat(1001)
    render(<TextAreaWithCounter {...defaultProps} value={longText} maxLength={1000} />)
    expect(screen.getByText(/exceeds maximum length by 1/)).toBeInTheDocument()
  })

  it('renders placeholder', () => {
    render(<TextAreaWithCounter {...defaultProps} placeholder="Enter text here" />)
    expect(screen.getByPlaceholderText('Enter text here')).toBeInTheDocument()
  })

  it('can be disabled', () => {
    render(<TextAreaWithCounter {...defaultProps} disabled />)
    expect(screen.getByRole('textbox')).toBeDisabled()
  })

  it('can be readOnly', () => {
    render(<TextAreaWithCounter {...defaultProps} readOnly />)
    expect(screen.getByRole('textbox')).toHaveAttribute('readonly')
  })

  it('shows correct count for zero chars', () => {
    render(<TextAreaWithCounter {...defaultProps} value="" maxLength={500} />)
    expect(screen.getByText('0 / 500')).toBeInTheDocument()
  })
})
