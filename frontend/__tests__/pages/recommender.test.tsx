import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

import RecommendPage from '../../app/(main)/admin/recommendations/page';
import { CartProvider } from '../../app/_contexts/CartContext';

// Mock supabase client before importing the page component
jest.mock('@/utils/supabase/client', () => ({
  createClient: () => ({
    auth: {
      getUser: async () => ({ data: { user: { id: 'u-test' } }, error: null }),
    },
    from: () => ({
      select: () => ({
        eq: () => ({
          single: async () => ({
            data: { id: 'u-test', name: 'Test User' },
            error: null,
          }),
        }),
      }),
    }),
  }),
}));

// Avoid jsdom navigation side-effects
const _origAnchorClick = HTMLAnchorElement.prototype.click;
beforeAll(() => {
  HTMLAnchorElement.prototype.click = function () {
    /* no-op */
  };
});
afterAll(() => {
  HTMLAnchorElement.prototype.click = _origAnchorClick;
});

describe('Admin Recommendations Page', () => {
  beforeEach(() => jest.resetAllMocks());

  it('shows validation error when query is empty', async () => {
    render(
      <CartProvider>
        <RecommendPage />
      </CartProvider>
    );

    const input = screen.getByRole('textbox');
    // Trigger Ctrl+Enter which the component listens for to submit
    fireEvent.keyDown(input, { key: 'Enter', ctrlKey: true });

    await waitFor(() => {
      expect(screen.getByText(/Please enter a query/i)).toBeInTheDocument();
    });
  });

  it('displays results when API returns recommendation', async () => {
    const fetchMock = jest.spyOn(global, 'fetch').mockImplementation((url: string | URL | Request) => {
      if (typeof url === 'string' && url.includes('/recommendations')) {
        return Promise.resolve({
          ok: true,
          headers: { get: () => 'application/json' },
          json: async () => ({ recommendation: 'Some results' }),
          text: async () => 'Some results',
        } as any);
      }
      return Promise.resolve({ ok: false } as any);
    });

    render(
      <CartProvider>
        <RecommendPage />
      </CartProvider>
    );

    const input = screen.getByRole('textbox');
    await userEvent.type(input, 'pizza near me');

    const btn = screen.getByRole('button', { name: /Get Recommendation/i });
    // Wait until the button becomes enabled (it is disabled when the query is empty)
    await waitFor(() => expect(btn).toBeEnabled());
    userEvent.click(btn);

    await waitFor(() => {
      expect(screen.getByText(/Some results/i)).toBeInTheDocument();
    });

    fetchMock.mockRestore();
  });
});
