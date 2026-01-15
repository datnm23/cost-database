# Frontend Testing Guide

This guide provides examples and patterns for testing the BOQ System frontend.

## Test Structure

```
frontend/
├── src/
│   ├── __tests__/           # Test files
│   │   ├── components/      # Component tests
│   │   ├── pages/           # Page tests
│   │   ├── services/        # Service tests
│   │   └── utils/           # Utility tests
│   ├── test/
│   │   ├── setup.ts         # Test setup
│   │   ├── mocks/           # Mock data
│   │   └── utils/           # Test utilities
```

## Setup

### 1. Install Testing Dependencies

All testing dependencies are already in `package.json`:
- `vitest` - Test runner
- `@testing-library/react` - React testing utilities
- `@testing-library/jest-dom` - DOM matchers
- `@vitest/ui` - Test UI
- `@vitest/coverage-v8` - Coverage reporting

### 2. Create Test Setup File

**`src/test/setup.ts`**
```typescript
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)

afterEach(() => {
  cleanup()
})
```

### 3. Configure Vitest

**`vitest.config.ts`**
```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

## Example Tests

### Component Tests

**`src/__tests__/components/Layout/MainLayout.test.tsx`**
```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import MainLayout from '@/components/Layout/MainLayout'

// Mock auth store
vi.mock('@/store/authStore', () => ({
  useAuthStore: () => ({
    user: { username: 'testuser', full_name: 'Test User' },
    logout: vi.fn(),
  }),
}))

describe('MainLayout', () => {
  it('renders children content', () => {
    render(
      <BrowserRouter>
        <MainLayout>
          <div>Test Content</div>
        </MainLayout>
      </BrowserRouter>
    )
    
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })

  it('displays user information', () => {
    render(
      <BrowserRouter>
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      </BrowserRouter>
    )
    
    expect(screen.getByText(/Test User/)).toBeInTheDocument()
  })

  it('navigates when menu item is clicked', () => {
    render(
      <BrowserRouter>
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      </BrowserRouter>
    )
    
    const projectsLink = screen.getByText('Projects')
    fireEvent.click(projectsLink)
    // Add navigation assertion
  })
})
```

### Page Tests

**`src/__tests__/pages/Dashboard.test.tsx`**
```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Dashboard from '@/pages/Dashboard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

const mockStats = {
  total_projects: 10,
  total_files: 25,
  total_line_items: 1500,
  verified_items: 1200,
  pending_items: 300,
  classification_accuracy: 95.5,
  recent_activity: [],
}

vi.mock('@/services/analyticsService', () => ({
  analyticsService: {
    getDashboardStats: vi.fn(() => Promise.resolve(mockStats)),
  },
}))

describe('Dashboard', () => {
  it('renders loading state initially', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    )
    
    expect(screen.getByText(/Loading dashboard/)).toBeInTheDocument()
  })

  it('displays statistics after loading', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    )
    
    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument() // total_projects
      expect(screen.getByText('25')).toBeInTheDocument() // total_files
    })
  })

  it('shows classification accuracy', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <Dashboard />
      </QueryClientProvider>
    )
    
    await waitFor(() => {
      expect(screen.getByText(/95.5/)).toBeInTheDocument()
    })
  })
})
```

### Service Tests

**`src/__tests__/services/projectService.test.ts`**
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { projectService } from '@/services/projectService'
import apiClient from '@/services/api'

vi.mock('@/services/api')

describe('projectService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getProjects', () => {
    it('fetches projects with default parameters', async () => {
      const mockProjects = [
        { id: 1, name: 'Project 1', status: 'active' },
        { id: 2, name: 'Project 2', status: 'planning' },
      ]

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockProjects })

      const result = await projectService.getProjects()

      expect(apiClient.get).toHaveBeenCalledWith('/projects?skip=0&limit=100')
      expect(result).toEqual(mockProjects)
    })

    it('includes status filter when provided', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: [] })

      await projectService.getProjects(0, 100, 'active')

      expect(apiClient.get).toHaveBeenCalledWith('/projects?skip=0&limit=100&status=active')
    })
  })

  describe('createProject', () => {
    it('creates a new project', async () => {
      const newProject = {
        name: 'New Project',
        client_name: 'Test Client',
        status: 'planning',
      }

      const mockResponse = { id: 1, ...newProject }
      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await projectService.createProject(newProject)

      expect(apiClient.post).toHaveBeenCalledWith('/projects', newProject)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteProject', () => {
    it('deletes a project', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({})

      await projectService.deleteProject(1)

      expect(apiClient.delete).toHaveBeenCalledWith('/projects/1')
    })
  })
})
```

### Integration Tests

**`src/__tests__/integration/FileUploadFlow.test.tsx`**
```typescript
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import FileUpload from '@/pages/FileUpload'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
})

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter>
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  </BrowserRouter>
)

describe('File Upload Flow', () => {
  it('completes full upload flow', async () => {
    const mockProjects = [
      { id: 1, name: 'Test Project', client_name: 'Test Client' },
    ]

    // Mock API calls
    vi.mock('@/services/projectService', () => ({
      projectService: {
        getProjects: vi.fn(() => Promise.resolve(mockProjects)),
      },
    }))

    render(<FileUpload />, { wrapper })

    // Step 1: Select project
    const projectSelect = screen.getByRole('combobox')
    fireEvent.click(projectSelect)
    
    await waitFor(() => {
      const option = screen.getByText('Test Project - Test Client')
      fireEvent.click(option)
    })

    // Step 2: Upload file
    const file = new File(['test'], 'test.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    const input = screen.getByRole('textbox', { hidden: true })
    fireEvent.change(input, { target: { files: [file] } })

    // Verify upload progress
    await waitFor(() => {
      expect(screen.getByText(/Uploading/)).toBeInTheDocument()
    })
  })
})
```

### Hook Tests

**`src/__tests__/hooks/useProjects.test.ts`**
```typescript
import { describe, it, expect, vi } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useQuery } from '@tanstack/react-query'
import { projectService } from '@/services/projectService'

vi.mock('@/services/projectService')

describe('useProjects hook', () => {
  it('fetches and returns projects', async () => {
    const mockProjects = [
      { id: 1, name: 'Project 1' },
      { id: 2, name: 'Project 2' },
    ]

    vi.mocked(projectService.getProjects).mockResolvedValue(mockProjects)

    const queryClient = new QueryClient()
    const wrapper = ({ children }: any) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    )

    const { result } = renderHook(
      () => useQuery({
        queryKey: ['projects'],
        queryFn: projectService.getProjects,
      }),
      { wrapper }
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockProjects)
  })
})
```

## Mock Data

**`src/test/mocks/projects.ts`**
```typescript
export const mockProjects = [
  {
    id: 1,
    name: 'Office Building Project',
    description: 'Construction of new office building',
    client_name: 'ABC Corporation',
    location: 'New York, NY',
    status: 'active',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    created_by: 1,
    file_count: 5,
    line_item_count: 250,
  },
  {
    id: 2,
    name: 'Bridge Construction',
    description: 'Highway bridge construction',
    client_name: 'State DOT',
    location: 'San Francisco, CA',
    status: 'planning',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
    created_by: 1,
    file_count: 2,
    line_item_count: 100,
  },
]
```

**`src/test/mocks/handlers.ts`**
```typescript
import { rest } from 'msw'
import { mockProjects } from './projects'

export const handlers = [
  rest.get('/api/v1/projects', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json(mockProjects))
  }),

  rest.post('/api/v1/projects', async (req, res, ctx) => {
    const body = await req.json()
    return res(
      ctx.status(201),
      ctx.json({
        id: 999,
        ...body,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
    )
  }),

  rest.delete('/api/v1/projects/:id', (req, res, ctx) => {
    return res(ctx.status(204))
  }),
]
```

## Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm run test -- src/__tests__/pages/Dashboard.test.tsx

# Run tests matching pattern
npm run test -- --grep="Dashboard"
```

## Coverage Reports

After running `npm run test:coverage`, view the report:

```bash
# Open HTML coverage report
open coverage/index.html

# View text summary in terminal
cat coverage/coverage-summary.txt
```

## Best Practices

### 1. **Test User Behavior, Not Implementation**
```typescript
// ❌ Bad - Testing implementation
expect(component.state.isLoading).toBe(false)

// ✅ Good - Testing user-visible behavior
expect(screen.getByText('Projects')).toBeInTheDocument()
```

### 2. **Use Testing Library Queries Properly**
```typescript
// Prefer in this order:
getByRole()        // Most accessible
getByLabelText()   // Forms
getByPlaceholderText()
getByText()
getByTestId()      // Last resort
```

### 3. **Test Async Operations**
```typescript
// Use waitFor for async operations
await waitFor(() => {
  expect(screen.getByText('Success')).toBeInTheDocument()
})
```

### 4. **Mock External Dependencies**
```typescript
// Mock API calls
vi.mock('@/services/api')

// Mock specific module
vi.mock('@/services/projectService', () => ({
  projectService: {
    getProjects: vi.fn(),
  },
}))
```

### 5. **Clean Up After Tests**
```typescript
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})
```

## Common Testing Patterns

### Testing Forms
```typescript
it('submits form with valid data', async () => {
  render(<ProjectForm onSubmit={mockSubmit} />)
  
  fireEvent.change(screen.getByLabelText('Project Name'), {
    target: { value: 'New Project' },
  })
  
  fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
  
  await waitFor(() => {
    expect(mockSubmit).toHaveBeenCalledWith({
      name: 'New Project',
    })
  })
})
```

### Testing Tables
```typescript
it('displays data in table', () => {
  render(<ProjectsTable data={mockProjects} />)
  
  expect(screen.getByText('Office Building Project')).toBeInTheDocument()
  expect(screen.getByText('Bridge Construction')).toBeInTheDocument()
})
```

### Testing Modals
```typescript
it('opens and closes modal', async () => {
  render(<Projects />)
  
  fireEvent.click(screen.getByText('Create Project'))
  expect(screen.getByRole('dialog')).toBeInTheDocument()
  
  fireEvent.click(screen.getByText('Cancel'))
  await waitFor(() => {
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
```

## Continuous Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: cd frontend && npm ci
        
      - name: Run tests
        run: cd frontend && npm run test:coverage
        
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          directory: ./frontend/coverage
```

## Next Steps

1. **Write tests for all pages**
   - Dashboard, Projects, FileUpload, LineItems, Analytics, Settings

2. **Add integration tests**
   - Complete user flows
   - API integration tests

3. **Set up E2E tests**
   - Consider Playwright or Cypress
   - Test critical user journeys

4. **Improve coverage**
   - Aim for 80%+ coverage
   - Focus on critical paths

5. **Add visual regression tests**
   - Consider Chromatic or Percy
   - Catch UI bugs early

---

**Happy Testing! 🧪**
