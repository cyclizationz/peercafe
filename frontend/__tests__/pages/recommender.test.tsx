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
    const fetchMock = jest
      .spyOn(global, 'fetch')
      .mockImplementation((url: string | URL | Request) => {
        if (typeof url === 'string' && url.includes('/recommendations')) {
          return Promise.resolve({
            ok: true,
            headers: { get: () => 'application/json' },
            json: async () => ({ recommendation: 'Some results' }),
            text: async () => 'Some results',
          } as any);
        }
        if (typeof url === 'string' && url.includes('/restaurants')) {
          return Promise.resolve({
            ok: true,
            headers: { get: () => 'application/json' },
            json: async () => [
              { restaurant_id: 1, name: 'Test Restaurant' },
              { restaurant_id: 2, name: 'Another Restaurant' },
            ],
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

  it('loads restaurants on mount', async () => {
    const fetchMock = jest
      .spyOn(global, 'fetch')
      .mockImplementation((url: string | URL | Request) => {
        if (typeof url === 'string' && url.includes('/restaurants')) {
          return Promise.resolve({
            ok: true,
            headers: { get: () => 'application/json' },
            json: async () => [
              { restaurant_id: 1, name: 'Bella Italia' },
              { restaurant_id: 2, name: 'Taco Fiesta' },
            ],
          } as any);
        }
        return Promise.resolve({ ok: false } as any);
      });

    render(
      <CartProvider>
        <RecommendPage />
      </CartProvider>
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost:8000/api/restaurants'
      );
    });

    fetchMock.mockRestore();
  });

  it('shows quick jump button when restaurant is found in recommendation', async () => {
    const fetchMock = jest
      .spyOn(global, 'fetch')
      .mockImplementation((url: string | URL | Request) => {
        if (typeof url === 'string' && url.includes('/recommendations')) {
          return Promise.resolve({
            ok: true,
            headers: { get: () => 'application/json' },
            json: async () => ({
              recommendation:
                'I recommend **Bella Italia** for great Italian food.',
            }),
          } as any);
        }
        if (typeof url === 'string' && url.includes('/restaurants')) {
          return Promise.resolve({
            ok: true,
            headers: { get: () => 'application/json' },
            json: async () => [
              { restaurant_id: 1, name: 'Bella Italia' },
              { restaurant_id: 2, name: 'Taco Fiesta' },
            ],
          } as any);
        }
        return Promise.resolve({ ok: false } as any);
      });

    render(
      <CartProvider>
        <RecommendPage />
      </CartProvider>
    );

    // Wait for restaurants to load
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        'http://localhost:8000/api/restaurants'
      );
    });

    const input = screen.getByRole('textbox');
    await userEvent.type(input, 'italian food');

    const btn = screen.getByRole('button', { name: /Get Recommendation/i });
    await waitFor(() => expect(btn).toBeEnabled());
    await userEvent.click(btn);

    await waitFor(
      () => {
        expect(screen.getByText(/Bella Italia/i)).toBeInTheDocument();
        const jumpButton = screen.getByRole('link', {
          name: /Go to Bella Italia/i,
        });
        expect(jumpButton).toBeInTheDocument();
        expect(jumpButton).toHaveAttribute('href', '/admin/restaurants/1');
      },
      { timeout: 3000 }
    );

    fetchMock.mockRestore();
  });

  it('handles restaurant loading error gracefully', async () => {
    const consoleErrorSpy = jest
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    const fetchMock = jest
      .spyOn(global, 'fetch')
      .mockImplementation((url: string | URL | Request) => {
        if (typeof url === 'string' && url.includes('/restaurants')) {
          return Promise.reject(new Error('Network error'));
        }
        return Promise.resolve({ ok: false } as any);
      });

    render(
      <CartProvider>
        <RecommendPage />
      </CartProvider>
    );

    // Should not crash, just log error
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });

    consoleErrorSpy.mockRestore();
    fetchMock.mockRestore();
  });
});
