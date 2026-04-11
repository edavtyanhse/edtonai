import { ApiClientError } from './client'

describe('ApiClientError', () => {
  it('has correct name', () => {
    const error = new ApiClientError('Not found', 404)
    expect(error.name).toBe('ApiClientError')
  })

  it('stores status code', () => {
    const error = new ApiClientError('Server error', 500)
    expect(error.status).toBe(500)
  })

  it('stores message', () => {
    const error = new ApiClientError('Forbidden', 403)
    expect(error.message).toBe('Forbidden')
  })

  it('stores detail', () => {
    const detail = { field: 'email', reason: 'invalid' }
    const error = new ApiClientError('Validation error', 422, detail)
    expect(error.detail).toEqual(detail)
  })

  it('is instance of Error', () => {
    const error = new ApiClientError('test', 400)
    expect(error).toBeInstanceOf(Error)
  })
})
