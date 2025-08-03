import '@testing-library/jest-dom'
import { mockImportMetaEnv } from './test-utils/mockImportMeta'

// Mock import.meta.env for tests
global.import = {
  meta: {
    env: mockImportMetaEnv
  }
} as any

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})