import { render, screen, fireEvent } from '@testing-library/react'
import CheckboxList from './CheckboxList'
import type { CheckboxOption } from '@/api/types'

const mockOptions: CheckboxOption[] = [
  {
    id: 'skill-1',
    label: 'Add Python',
    description: 'Add Python to skills section',
    category: 'skills',
    impact: 'high',
    requires_user_input: false,
    user_input_placeholder: null,
  },
  {
    id: 'exp-1',
    label: 'Add project experience',
    description: 'Describe relevant project',
    category: 'experience',
    impact: 'medium',
    requires_user_input: true,
    user_input_placeholder: 'Describe your project...',
  },
  {
    id: 'ats-1',
    label: 'Add keywords',
    description: 'Add missing ATS keywords',
    category: 'ats',
    impact: 'low',
    requires_user_input: false,
    user_input_placeholder: null,
  },
]

describe('CheckboxList', () => {
  const defaultProps = {
    options: mockOptions,
    selected: [] as string[],
    onChange: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders all options', () => {
    render(<CheckboxList {...defaultProps} />)
    expect(screen.getByText('Add Python')).toBeInTheDocument()
    expect(screen.getByText('Add project experience')).toBeInTheDocument()
    expect(screen.getByText('Add keywords')).toBeInTheDocument()
  })

  it('groups options by category', () => {
    render(<CheckboxList {...defaultProps} />)
    expect(screen.getByText('Навыки')).toBeInTheDocument()
    expect(screen.getByText('Опыт')).toBeInTheDocument()
    expect(screen.getByText('ATS оптимизация')).toBeInTheDocument()
  })

  it('calls onChange when option is toggled on', () => {
    render(<CheckboxList {...defaultProps} />)
    fireEvent.click(screen.getByText('Add Python'))
    expect(defaultProps.onChange).toHaveBeenCalledWith(['skill-1'])
  })

  it('calls onChange when option is toggled off', () => {
    render(<CheckboxList {...defaultProps} selected={['skill-1']} />)
    fireEvent.click(screen.getByText('Add Python'))
    expect(defaultProps.onChange).toHaveBeenCalledWith([])
  })

  it('shows impact badges', () => {
    render(<CheckboxList {...defaultProps} />)
    expect(screen.getByText('важно')).toBeInTheDocument()
    expect(screen.getByText('средне')).toBeInTheDocument()
    expect(screen.getByText('низкий')).toBeInTheDocument()
  })

  it('shows empty state when no options', () => {
    render(<CheckboxList options={[]} selected={[]} onChange={vi.fn()} />)
    expect(screen.getByText('Нет доступных улучшений')).toBeInTheDocument()
  })

  it('shows user input badge for options requiring input', () => {
    render(<CheckboxList {...defaultProps} />)
    expect(screen.getByText('нужен ваш ввод')).toBeInTheDocument()
  })

  it('shows descriptions', () => {
    render(<CheckboxList {...defaultProps} />)
    expect(screen.getByText('Add Python to skills section')).toBeInTheDocument()
    expect(screen.getByText('Add missing ATS keywords')).toBeInTheDocument()
  })
})
